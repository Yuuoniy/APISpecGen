import re
import sys
from utils.CodeSearcher import CodeSearcher


class SpecGenerator:
    def __init__(self):
        pass   
    
                
    def infer_postOp_for_inferred_API(self, inferred_API, seedSecOp,inferred_critical_var,repo_name,propo_direction):
        count = self.__find_spec_usage(inferred_API, seedSecOp,inferred_critical_var,repo_name)
        if count:
            return seedSecOp,count
        
        # the following is a quick check for speedup
        alternative_op = self.__get_alternative_operation(inferred_API)
        if alternative_op:
            count = self.__find_spec_usage(inferred_API, alternative_op, inferred_critical_var,repo_name)
            if count:
                return alternative_op, count
        
        # find possible seed op
        inferred_secop = self.__find_possible_secOp(inferred_API, seedSecOp,inferred_critical_var,repo_name)
        if inferred_secop is not None:
            count = self.__find_spec_usage(inferred_API, seedSecOp,inferred_critical_var,repo_name)
            
            if propo_direction == 'succ':
                is_data_related = self.__validate_the_inferred_secop(inferred_secop,seedSecOp)
            elif propo_direction == 'pre':
                is_data_related = True

            if is_data_related:
                return inferred_secop,count
            
        return None, 0
    
    def __find_spec_usage(self, target_API,sec_op,critical_var,repo_name) -> bool:
       
        if critical_var == 'retval':
            query = f'$ret = {target_API}();{sec_op}(_($ret));'
        elif critical_var=='arg':
            query = f'{target_API}($arg);{sec_op}(_($arg));'
        
        data = CodeSearcher(repo_name).query_code(query)
        usage_count = len(func := CodeSearcher(repo_name).split_weggli_data(data))
        if usage_count==0 and critical_var=='arg':
            query = f'{target_API}(_($arg));{sec_op}(_($arg));'
            data = CodeSearcher(repo_name).query_code(query)
            return len(func := CodeSearcher(repo_name).split_weggli_data(data))
        return usage_count
    

    def __get_alternative_operation(self, api):
        if 'get' in api:
            return api.replace('get', 'put')
        elif 'alloc' in api:
            return api.replace('alloc', 'free')
        elif 'inc' in api:
            return api.replace('inc', 'dec')
        return None
    


    def __find_possible_secOp(self,inferred_API, seedSecOp,critical_var, repo_name):
        if critical_var=='retval':
            query = f'$ret={inferred_API}(); $possible_sec_op($ret);'
            possible_sec_ops = CodeSearcher("linux").weggli_get_desired_filed(query,'possible_sec_op')
        
        
        elif critical_var =='arg':
            query1 = f'{inferred_API}($arg); $possible_sec_op($arg);'
            query2 = f'{inferred_API}(&$arg); $possible_sec_op(&$arg);'

            possible_sec_ops = CodeSearcher("linux").weggli_get_desired_filed(query1,'possible_sec_op')
            possible_sec_ops += CodeSearcher("linux").weggli_get_desired_filed(query2,'possible_sec_op')
        
        for possible_sec_op in possible_sec_ops:
            subwords = possible_sec_op.split('_')
            keys = ['put','free','dec']
            
            if any(key in subwords for key in keys):
                return possible_sec_op
        
        return None

    def __validate_the_inferred_secop(self,pre_secOp,succ_secOp):
        query =  f'_ {pre_secOp}(_ *$var){{{succ_secOp}(_($var));}}'
        return len(func := CodeSearcher('linux').weggli_get_found_func(query))

