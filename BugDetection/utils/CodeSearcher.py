import sys
import uuid
import configparser
import os
import re
import subprocess

from utils.ASTParser import ASTParser
from config import cp


class CodeSearcher:
    def __init__(self, repo_name):
        self.source_dir = cp.get('URL',repo_name)
    
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
        file = uuid.uuid4().hex
        cmd = f"weggli '{query}' {self.source_dir} -A 500 -B 500 -l > {file}"
        os.system(cmd)
        try:
            data= open(file).read()
            
        except Exception:
            data = ''
        
        os.system(f'rm {file}')
        
        return data
    
        
    def weggli_get_found_with_code(self, query):
        data = self.query_code(query)
        func = self.split_weggli_data_with_code(data)
        return func

    def __weggli_get_found_func(self, query):
        data = self.query_code(query)
        func = self.split_weggli_data(data)
        return func

    def weggli_get_found_func(self, query):
        try:
            return list(set(self.__weggli_get_found_func(query)))
        except Exception as e:
            print(e)
            return []
    
