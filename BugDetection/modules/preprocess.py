import re
import networkx as nx
from networkx.drawing import nx_agraph
import shutil
import os
import subprocess
from multiprocessing import Pool
from config import DETECTOR_WORK_ROOT,DETECTOR_DATA_ROOT
from config import cp,ic
from rich.progress import track


from utils import tree_sitter_helper
from utils.CodePreProcess import CodePreProcessor
import logging
logger = logging.getLogger('detector')



def get_func_name_from_def(code):
    tree = tree_sitter_helper.parser.parse(bytes(code, "utf8"))
    funcs = tree_sitter_helper.find_node_by_type(tree,"function_declarator")
    if len(funcs) == 0:
        return ''

    return tree_sitter_helper.get_node_content(funcs[0].child_by_field_name("declarator"), code)
    
class Preprocess:
    WORK_ROOT = DETECTOR_WORK_ROOT
    def __init__(self,repo_name,key_func,quick=True):
        self.repo_name = repo_name
        self.source_dir = cp.get('URL',repo_name)
        
        self.quick = quick
        
        self.main_api = key_func
        self.REPO_DATA_ROOT = os.path.join(DETECTOR_DATA_ROOT,self.repo_name)
        self.Preprocess_main()

    def Preprocess_main(self):
        
        if os.path.exists(f'{self.REPO_DATA_ROOT}/{self.main_api}'):
            # return
            if self.quick:
                return
            shutil.rmtree(f"{self.REPO_DATA_ROOT}/{self.main_api}", ignore_errors=True)
            
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.main_api}')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/def')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/cfg-outdir')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/pdg-outdir')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/simple_cfg')
        self.get_caller_of_context()
        self.split_data(f'{self.REPO_DATA_ROOT}/{self.main_api}/{self.main_api}_callsite')
        if not os.listdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/def'):
            return
        self.call_joern()
        self.process_dot_files()


    def get_caller_of_context(self):
        cmd = f"weggli '{self.main_api}();' {self.source_dir} -A 500 -B 500 -l > {self.REPO_DATA_ROOT}/{self.main_api}/{self.main_api}_callsite"
        # ic(cmd)
        os.system(cmd)

    def split_data(self,file):
        ic()
        data = open(file).read()
        pattern = rf"{self.source_dir}.*\n"
        res = re.split(pattern,data)
        callers_of_main_api = []
        
        for func in res:
            if len(func) == 0:
                continue
            func = CodePreProcessor.clean_code(func)
            funcname = get_func_name_from_def(func)
            if funcname=='':
                continue
            callers_of_main_api.append(funcname)
            open(f'{self.REPO_DATA_ROOT}/{self.main_api}/def/{funcname}.c','w+').write(func)

        # dump list
        ic(len(callers_of_main_api))
        with open(f'{self.REPO_DATA_ROOT}/{self.main_api}/caller_of_{self.main_api}.txt','w+') as f:
            for func in callers_of_main_api:
                f.write(f'{func}\n')


    def call_joern(self):
        cmd1 = f'joern-parse  {self.REPO_DATA_ROOT}/{self.main_api}/def -o {self.REPO_DATA_ROOT}/{self.main_api}/cpg.bin '
        os.system(cmd1)
        if os.path.exists(f"{self.REPO_DATA_ROOT}/{self.main_api}/cfg-outdir"):
            shutil.rmtree(f"{self.REPO_DATA_ROOT}/{self.main_api}/cfg-outdir", ignore_errors=True)
        if os.path.exists(f"{self.REPO_DATA_ROOT}/{self.main_api}/pdg-outdir"):
            shutil.rmtree(f"{self.REPO_DATA_ROOT}/{self.main_api}/pdg-outdir", ignore_errors=True)
        cmd1 = f'joern-export  --repr cfg {self.REPO_DATA_ROOT}/{self.main_api}/cpg.bin --out {self.REPO_DATA_ROOT}/{self.main_api}/cfg-outdir'
        cmd2 = f'joern-export  --repr pdg {self.REPO_DATA_ROOT}/{self.main_api}/cpg.bin --out {self.REPO_DATA_ROOT}/{self.main_api}/pdg-outdir'
        # ic(cmd1)
        # ic(cmd2)
        os.system(cmd1)
        os.system(cmd2)


    def process_dot_files(self,type='cfg'):
        dot_files = os.listdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/{type}-outdir')
        dot_files = [x for x in dot_files if x.endswith('.dot')]
        funcs = open(f'{self.REPO_DATA_ROOT}/{self.main_api}/caller_of_{self.main_api}.txt','r').read().split('\n')
        os.chdir(f'{self.REPO_DATA_ROOT}/{self.main_api}/{type}-outdir')
        p = Pool(processes=32)
        for dot_file in track(dot_files):
            #print(dot_file)
            p.apply_async(self.process_dot_file_one,(dot_file,funcs,type))
        p.close()
        p.join()
        os.chdir(f'{self.WORK_ROOT}')
        
    def process_dot_file_one(self, dot_file, funcs, type):
        G = nx.drawing.nx_agraph.read_dot(f'{self.REPO_DATA_ROOT}/{self.main_api}/{type}-outdir/{dot_file}')

        if G.name not in funcs:
            os.system(f"rm {dot_file}")
        else:
            os.system(f"mv {dot_file} {G.name}.dot")
            
            
class PreprocessSingleFunc():

    WORK_ROOT = cp.get('DETECTOR','work')
    def __init__(self, repo_name, main_api,test_func):
        self.source_dir = cp.get('URL',repo_name)
        self.test_func = test_func
        self.main_api = main_api
        self.DATA_ROOT = os.path.join(cp.get('DETECTOR','data'),repo_name)
    
        self.Preprocess_main()
        
        
    def Preprocess_main(self):
        
        self.get_caller_of_context()
        self.call_joern()
        self.process_dot_files()
    
    def get_caller_of_context(self):
        if os.path.exists(f'{self.DATA_ROOT}/{self.main_api}'):
            shutil.rmtree(f"{self.DATA_ROOT}/{self.main_api}", ignore_errors=True)
            
        os.mkdir(f'{self.DATA_ROOT}/{self.main_api}')
        os.mkdir(f'{self.DATA_ROOT}/{self.main_api}/def')
        os.mkdir(f'{self.DATA_ROOT}/{self.main_api}/cfg-outdir')
        os.mkdir(f'{self.DATA_ROOT}/{self.main_api}/pdg-outdir')
        os.mkdir(f'{self.DATA_ROOT}/{self.main_api}/simple_cfg')
        cmd = f"weggli '{self.main_api}();' {self.source_dir} -A 500 -B 500 -l > {self.DATA_ROOT}/{self.main_api}/{self.main_api}_callsite"
        ic(cmd)
        os.system(cmd)
        self.split_data(f'{self.DATA_ROOT}/{self.main_api}/{self.main_api}_callsite')
        
    
    def call_joern(self):
        bin_file = f'{self.DATA_ROOT}/{self.main_api}/{self.test_func}_cpg.bin'
        if os.path.exists(bin_file):
            return
        source = f'{self.DATA_ROOT}/{self.main_api}/def/{self.test_func}.c'
        parse_cmd = f'joern-parse  {source} -o {bin_file}'
        os.system(parse_cmd)
        print(parse_cmd)

        outdir = f'{self.DATA_ROOT}/{self.main_api}/cfg-{self.test_func}-outdir'
        # check if the outdir exist, if exist, then remove it
        if os.path.exists(outdir):
            shutil.rmtree(outdir, ignore_errors=True)
            
        
        input_file_abs = os.path.abspath(bin_file)
        output_dir_abs = os.path.abspath(outdir)

        export_cmd = f'joern-export  --repr cfg {input_file_abs} --out {output_dir_abs}'

        ic(export_cmd)
        print("testing....")
        # os.system(export_cmd)
    
        # Run the shell command and capture the output
        result = subprocess.check_output(export_cmd, shell=True)
        print(result.decode('utf-8'))
        # Check whether the process completed successfully

    
    def process_dot_files(self,type='cfg'):
        try:
            cfg_dir = f'{self.DATA_ROOT}/{self.main_api}/cfg-{self.test_func}-outdir'
            dot_files = [x for x in os.listdir(cfg_dir) if x.endswith('.dot')]
            os.chdir(cfg_dir)
            for dot_file in track(dot_files):
                self.process_dot_file_one(cfg_dir,dot_file,type)
        
            os.chdir(f'{self.WORK_ROOT}')
        except Exception as e:
            ic(e)
            logger.error(e)
        
    def split_data(self,file):
        data = open(file).read()
        pattern = rf"{self.source_dir}.*\n"
        res = re.split(pattern,data)
        callers_of_main_api = []
        
        for func in res:
            if len(func) == 0:
                continue
            func = CodePreProcessor.clean_code(func)
            funcname = get_func_name_from_def(func)
            if funcname=='':
                continue
            callers_of_main_api.append(funcname)
            open(f'{self.DATA_ROOT}/{self.main_api}/def/{funcname}.c','w+').write(func)

        # dump list
        ic(len(callers_of_main_api))
        with open(f'{self.DATA_ROOT}/{self.main_api}/caller_of_{self.main_api}.txt','w+') as f:
            for func in callers_of_main_api:
                f.write(f'{func}\n')
                
    def process_dot_file_one(self, cfg_dir, dot_file, type):
       
        G = nx.drawing.nx_agraph.read_dot(f'{cfg_dir}/{dot_file}')

        if G.name not in [self.test_func]:
            os.system(f"rm {dot_file}")
        else:
            os.system(f"mv {dot_file} ../cfg-outdir/{G.name}.dot")
    
