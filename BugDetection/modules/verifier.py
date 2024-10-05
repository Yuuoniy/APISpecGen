import subprocess
import os
import sys
# sys.path.append("/root/similar-bug/APIClustering/") 
# from global_vars import *
from config import DETECTOR_DATA_ROOT,ic

import logging

logger = logging.getLogger('detector')



class ReportVerifier:
    # verifier to reduce false positives
    # 
    def __init__(self,rule,test_func,violated_path_num,critical_variable):
        try:
            self.main_api = rule['main_api']
            self.var_type = rule['var_type']
            self.REPO_DATA_ROOT = os.path.join(DETECTOR_DATA_ROOT,rule['repo_name'])
            self.code_file = f'{self.REPO_DATA_ROOT}/{self.main_api}/def/{test_func}.c'
            self.sec_op = rule['sec_op']
            self.repo_name = rule['repo_name']
            self.api_status = rule['api_status']
            self.violated_path_num = violated_path_num
            self.critical_variable = critical_variable
        except Exception as e:
            logger.error(e)
            ic(e)
        
    
    
    def check(self) -> bool:
        if self.var_type == 'retval':
            isFP = False
            if isFP := self.has_var_constraints():
                return isFP
            if isFP := self.has_callback():
                return isFP
            if isFP := (self.has_retval_check() and self.violated_path_num == 1 and self.api_status == 'success'):
                return isFP
        return False
    
    def has_retval_check(self) -> bool:
        # if the main api has retval check, violate path num should larger than 1
        query1 = f"weggli '$ret={self.main_api}();if(!$ret)_;' {self.code_file}"
        query2 = f"weggli '$ret={self.main_api}();if($ret==NULL)_;' {self.code_file}"
        query3 = f"weggli '$ret={self.main_api}();if($ret<0)_;' {self.code_file}"
        # query3 = f"weggli '$ret={self.main_api}();if($ret!=NULL)_;' {self.code_file}"
        # ic(query1,query2)
        res1 = self.run_query(query1)
        res2 = self.run_query(query2)
        res3 = self.run_query(query3)
        return len(res1) > 0 or len(res2) > 0 or len(res3) > 0
    
    def has_var_constraints(self) -> bool:
        # ic(self.code_file)
        sec_ops = self.sec_op.split('|')
        for sec_op in sec_ops:
            query1 = f"weggli '$ret={self.main_api}();if($ret)_; {sec_op}($ret);' {self.code_file}"
            query2 = f"weggli '$ret={self.main_api}();if($ret!=-1)_; {sec_op}($ret);' {self.code_file}"
            query3 = f"weggli '$ret={self.main_api}();if($ret!=NULL)_; {sec_op}($ret);' {self.code_file}"
            query4 = f"weggli 'if(_($var)){{ {sec_op}($var);}}' {self.code_file}"
            
            
            # if (ret) # platform_device_put(vpac270_pcmcia_device);
            query5 = f"weggli 'strict: if(_) {sec_op}();' {self.code_file}"
            
            # ic(query1,query2,query3)
            res1 = self.run_query(query1)
            res2 = self.run_query(query2)
            res3 = self.run_query(query3)
            res4 = self.run_query(query4)
            res5 = self.run_query(query5)
            
            if(len(res1) > 0 or len(res2) > 0 or len(res3) > 0) or len(res4) > 0 or len(res5) > 0:
                return True
        return False
    

    def has_callback(self)->bool:
        query = f"weggli -R 'callback_func=add_action_or_reset$' '{self.main_api}(); $callback_func();' {self.code_file}"
        res = self.run_query(query)
        return len(res) > 0
    
    @classmethod
    def run_query(cls,cmd):
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        # ic(res)
        return result.stdout.read().decode().split('\n')[0]
    
    
    def var_is_autofree(self):
        pass
    
