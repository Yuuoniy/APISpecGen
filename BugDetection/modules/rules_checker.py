
import re
import networkx as nx
import os
from rich.progress import track
import pandas as pd
from icecream import ic
import sys
from multiprocessing import Pool
from multiprocessing import cpu_count
import utils.cfg_analyzer as cfg_analyzer
from utils import tree_sitter_helper
import time
from typing import List
import timeout_decorator
from modules.verifier import ReportVerifier
import traceback
from config import DETECTOR_DATA_ROOT,cp,BUG_REPORT_FILE,CHK_BUG_REPORT_FILE
import sys
from utils.CodeSearcher import CodeSearcher

import logging

# logging.basicConfig(filename=os.path.join(DATA_ROOT,'detector.log'),level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(funcName)s %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S',filename=os.path.join(DATA_ROOT,'detector.log'),level=logging.DEBUG)

# # logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# # set the logger name
# logger.name = 'detector'

logger = logging.getLogger('detector')


# report_file_name = 'bug_report.csv'

class RuleCheckerSingle:
    methods = []
    funcs_cfg =['(METHOD_RETURN,','(METHOD,' ,'(RETURN,',] 
    critical_variable = ''


    def __init__(self,rule,critical_var='',varScope='',func_def=''):
        self.rule = rule
        self.repo_name = rule['repo_name']
        self.source_dir = cp.get('URL',self.repo_name)
        
        self.main_api = rule['main_api']
        self.sec_op = rule['sec_op'].split("|")
        self.var_type = rule['var_type']
        self.api_status = rule['api_status']
        self.path_type = rule['path_type']
        self.critical_variable = critical_var
        self.varScope = varScope
        self.func_def = func_def
        self.REPO_DATA_ROOT = os.path.join(DETECTOR_DATA_ROOT,self.repo_name)
        
    
    def check(self,test_func)->bool:
        isBuggy = self.check_security_operations_for_func(test_func)
     
    def verifier_report_is_FP(self,func,violated_path_num)->bool:
        # autofree
        if tree_sitter_helper.is_autofree_var(self.func_def,self.critical_variable):
            return True
        try:
            ver = ReportVerifier(self.rule,func,violated_path_num,self.critical_variable)
            return ver.check()
        except Exception as e:
            traceback.print_exc()
            ic(e)
            logger.error(e)
            
    
    
    def check_if_has_wrapper_sec_op(self,violate_paths,dot_file):
        G = nx.drawing.nx_agraph.read_dot(dot_file)
        to_check_funcs = self.get_all_funcs_in_path(G)
        return any(self.func_has_sec_op_inside(func[0]) for func in to_check_funcs)
        
    
    def func_has_sec_op_inside(self,func) -> bool:
        # sec_ops = self.sec_op.split('|')
        for sec_op in self.sec_op:
            query = f"weggli '_ {func}(_){{{sec_op}($ret);}}' {self.source_dir}"
            # ic(query)
            if res := ReportVerifier.run_query(query):
                return True
    
    def get_all_funcs_in_path(self,G):
        funcs = []
        keywords = ['free','clean','remove']
        # iterate all labels in G
        labels = list(nx.get_node_attributes(G, "label").values())
        for label in labels:
            stmt = label.split(',',1)[1][:-1]
            func,args,code = tree_sitter_helper.get_func_name_and_args(stmt)
            if func:
                funcs.append((func, args, code))
        return [func for func in funcs if any(keyword in func[0] for keyword in keywords)]
        
    
    def check_security_operations_for_func(self,test_func,critical_var = '',dot_file=None,write=True):
        # pdb.set_trace()
        dot_file = dot_file if dot_file is not None else self.get_dot_file(test_func)
        if not os.path.exists(dot_file):
            ic(f'file {dot_file} not exist')
            logger.error(f'file {dot_file} not exist')
            return False
        try:
            # ic(f"{test_func}")
            violate_paths = self.get_violate_paths(dot_file)
            # ic(violate_paths.count(False))
         
            if self.check_violate_paths_by_type(violate_paths):
                return self.confirm_bug_report(violate_paths, test_func, dot_file, write)

            # print(f"[checked report] {test_func} not lack security operation for {self.main_api}")
            return False
        except Exception as e:
            ic(test_func,dot_file,e)
            logger.error(e)
            traceback.print_exc()
            return False

    # TODO Rename this here and in `check_security_operations_for_func`
    def confirm_bug_report(self, violate_paths, test_func, dot_file, write):
        # futher check
        violated_path_num = violate_paths.count(False)
        if(self.verifier_report_is_FP(test_func,violated_path_num)):
            # print(f"[checked report] | {test_func} not lack security operation for {self.main_api}(FP)")   
            return False

        # check if perform alternative sec_op
        if(self.check_if_has_wrapper_sec_op(violate_paths,dot_file)):
            # print(f"[checked report] {test_func} not lack security operation for {self.main_api}(FP, wrapper)")   
            return False

        if write:
            self.record_buggy_site(test_func,violated_path_num)
        print(f"[checked report] {test_func} may lack post-operation ({self.sec_op}) for {self.main_api}")
        return True

    def get_violate_paths(self,dot_file):
        # check if file exist


        error_paths,non_error_paths = self.sort_paths(dot_file)
        G = nx.drawing.nx_agraph.read_dot(dot_file)

        tested_paths = self.get_satisfied_paths(G,error_paths,non_error_paths)
        # ic(tested_paths)
        if tested_paths is None or len(tested_paths) == 0:
            return []
        return [self.check_operations_in_path(G,path,False) for path in tested_paths]


    def check_violate_paths_by_type(self,violate_paths):
        if self.path_type == 'error' and self.api_status =='none':
            return violate_paths.count(False) >= 1
        
        if self.path_type == 'error':
            return violate_paths.count(False) > 1
        
        if self.path_type == 'all':
            return violate_paths.count(False) >= 1
        
    

    def get_dot_file(self,test_func):
        return f"{self.REPO_DATA_ROOT}/{self.main_api}/simple_cfg/{test_func}-{self.main_api}.dot"

    def record_buggy_site(self,test_func,violated_path_num):
        sec_ops = "|".join(self.sec_op)
        # cols = ['repo_name','test_func','main_api','sec_op','var_type','var','isLocal','violated_path_num']
        # cols = 
        cols=['repo_name','test_func','main_api','sec_op','var_type','var','scope','violated_path_num']
        bug_item = pd.DataFrame([[self.repo_name, test_func,self.main_api,sec_ops,self.var_type, self.critical_variable, self.varScope,violated_path_num]],columns=cols)
        # write_path = f"{self.REPO_DATA_ROOT}/{BUG_REPORT_FILE}"
        # ic(write_path)
        # set column name if not exist
        
        bug_item.to_csv(BUG_REPORT_FILE,mode='a+',index=False,header=not os.path.exists(BUG_REPORT_FILE))


    
    def get_satisfied_paths(self,G,error_paths,non_error_paths):
        if self.path_type == 'error':
            return error_paths
        return error_paths+non_error_paths

    def check_operations_in_path(self,G,path,is_error=False):
        # print("check_operations_in_path")
        # print(self.sec_op)
        for node in path:
            # if any(func in labels[node] for func in self.funcs_cfg):
            # print(G.nodes[node]['label'])
            if any(sec_op in G.nodes[node]['label'] for sec_op in self.sec_op):
                if is_error:  
                    cfg_analyzer.format_path(G,path)
                return True
        return False

    def sort_paths(self,dot_file):
        G = nx.drawing.nx_agraph.read_dot(dot_file)
        if G.number_of_nodes() == 0:
            # ic("emprty graph",dot_file)
            return [],[]
        source = list(nx.topological_sort(G))[0]
        target = cfg_analyzer.node_id_by_label(G,'METHOD_RETURN')
        error_paths = []
        non_error_paths = []
        escape_paths = [] # these path return critical variable
        paths = list(nx.all_simple_paths(G, source=source, target=target))
        
        return_nodes_in_paths = [cfg_analyzer.get_return_node(G,path) for path in paths]
        # ic(return_nodes_in_paths)
        # pdb.set_trace()
        
        has_zero_ret = 0
        for node in return_nodes_in_paths:
            if 'return 0' in node['label']:
                has_zero_ret = 1
                break
        
        for path in paths:
            cfg_analyzer.format_path(G,path)
            if cfg_analyzer.check_is_error_path(G,path):
                error_paths.append(path)
            elif cfg_analyzer.check_is_escaped_path(G,path,self.critical_variable):
                escape_paths.append(path) # to test
            else:
                # we check non-error path, which return value is 0; if the non-error paths is not empty, then the remaining paths are considered to be error paths.
                # this is for the case that non-error path return 0; while error path return ret;
                # we still need to fix this, maybe all path return ret; but we can not know which path is error path. maybe we can regard one path is non-error and the other paths are error.
                # FIXME: we need to check if return 0; exist at first, otherwise, return ret will classify as non-error path because we evaluate it because it occurs before 'return 0';
                if cfg_analyzer.check_is_non_error_path(G,path):
                    non_error_paths.append(path)
                elif len(non_error_paths) and cfg_analyzer.check_is_uncertain_path(G,path):
                    error_paths.append(path)
                elif has_zero_ret == 0:
                    non_error_paths.append(path)
                else:
                    error_paths.append(path)
                # non_error_paths.append(path)    

        # we have three situtaions:
        # 1. absoulte error path, which is error path and return value has 'err' or negative value
        # 2. absolute non-error path, which is non-error path and return value is 0
        # 3. uncertain path, which is 'return ret'
        self.print_path_info(G,error_paths,non_error_paths,escape_paths)

        return error_paths,non_error_paths

    



    def print_path_info(self,G,error_paths,non_error_paths,escape_paths):
        # ic(len(error_paths),len(non_error_paths),len(escape_paths))
        for path in error_paths:
            # ic("error paths")
            cfg_analyzer.print_return_node_in_path(G,path)
        for path in escape_paths:
            # ic("escape paths")
            cfg_analyzer.print_return_node_in_path(G,path)
        for path in non_error_paths:
            # ic("non-error paths")
            cfg_analyzer.print_return_node_in_path(G,path)
            
  
    
class chkCheckerSingle:
    def __init__(self,rule):
        self.repo_name = rule['repo_name']
        self.source_dir = cp.get('URL',self.repo_name)
        self.main_api = rule['API']
        self.sec_op = rule['SecOp']
        self.var_type = 'retval'
        self.bug_report_file = None
    
    
    def check(self):
        buugy_funcs = self.generate_query_stmt()
        self.report_bugs(buugy_funcs)
    
        
    def generate_query_stmt(self)->str:
        query= f'$ret = {self.main_api}(); NOT: $ret=$c(); NOT: if(IS_ERR($ret))_;if(!$ret)_; NOT: if(IS_ERR($ret))_;'
        buggy_funcs = CodeSearcher(self.repo_name).weggli_get_found_func(query)
        return buggy_funcs
        
        

    def report_bugs(self,funcs):
        for buggy_func in funcs:
            bug_item = pd.DataFrame([[buggy_func,self.main_api,self.sec_op,self.var_type]],columns=['buggy_func','main_api','sec_op','var_type'])
            bug_item.to_csv(CHK_BUG_REPORT_FILE,mode='a+',index=False,header=False)
