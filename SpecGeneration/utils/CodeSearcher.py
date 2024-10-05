
import uuid
import os
import re
from utils.ASTParser import ASTParser
# ic.configureOutput(includeContext=True)
from config import cp
import subprocess
from collections import Counter
import json

class CodeSearcher:
    def __init__(self, repo_name):
        self.source_dir = cp.get('URL',repo_name)
        self.weggli_path = 'weggli'
    
    def split_weggli_data(self, data):
        pattern = rf"{self.source_dir}.*\n"
        res = re.split(pattern,data)
        callers_of_main_api = []
        for i in range(len(res)):
            if len(res[i]) == 0:
                continue
            funcname = ASTParser.get_func_name_from_def(res[i])
            if funcname=='':
                continue
            callers_of_main_api.append(funcname)
        return callers_of_main_api
    
    def split_weggli_data_with_code(self, data)->dict:
        func_code_dict = {}
        pattern = rf"{self.source_dir}.*\n"
        res = re.split(pattern,data)
        for func in res:
            if len(func) == 0:
                continue
            funcname = ASTParser.get_func_name_from_def(func)
            if funcname=='':
                continue
            func_code_dict[funcname] = func
        return func_code_dict


    def query_code(self, query):
        directory_path = ".code_query_tmp_results"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        file = os.path.join(directory_path,uuid.uuid4().hex)
        cmd = f"weggli '{query}' {self.source_dir} -A 500 -B 500 -l > {file}"
        os.system(cmd)
        try:
            data= open(file).read()
            
        except Exception:
            data = ''
        
        os.system(f'rm {file}')
        
        return data
    
    
    def query_code_with_log_to_file(self,query, out_file):
        cmd = f"{self.weggli_path} '{query}' {self.source_dir} -s {out_file}"
        
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        res = result.stdout.read().decode().split('\n')[0]
        return len(res) > 0
    
    def weggli_get_found_with_code(self, query):
        data = self.query_code(query)
        func = self.split_weggli_data_with_code(data)
        return func

    def __weggli_get_found_func(self, query):
        data = self.query_code(query)
        func = self.split_weggli_data(data)
        return func

    def weggli_get_founc_callee(self,query):
        directory_path = ".code_query_tmp_results"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        file = os.path.join(directory_path,uuid.uuid4().hex)
        self.query_code_with_log_to_file(query,file)
        callees = self.__parse_to_get_field(file,'callee')
        return callees
    
    def weggli_get_desired_filed(self,query,field):
        directory_path = ".code_query_tmp_results"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        file = os.path.join(directory_path,uuid.uuid4().hex)
        self.query_code_with_log_to_file(query,file)
        vals = self.__parse_to_get_field(file,field)
        return vals
    
    
    def __parse_to_get_field(self,outfile,field):
        try:
            with open(outfile, 'r') as file:
                data = json.load(file)

            vals = []
            for file_set in data:
                for file_entry in file_set:
                    for match_group in file_entry['matches']:
                        for match in match_group['vars']:
                            if match['var'] == '$'+field:
                                vals.append(match['val'])
        except Exception as e:
            print(e)
            vals = []

        return vals
    
    
    def weggli_get_found_func(self, query):
        try:
            return list(set(self.__weggli_get_found_func(query)))
        except Exception as e:
            print(e)
            return []
    
