from utils.CodeSearcher import CodeSearcher
from utils import ASTParser
from QuickMode.Spec import APISpec
from config import WORKDIR
import os


ignored_ops_file = os.path(WORKDIR,'SpecGeneration/irrelvant_ops.txt')

class SpecPropogatePre:
    
    def __init__(self, spec):
        self.seed_api = spec.API
        self.secOp = spec.secOp
        
        self.critical_var = spec.critical_var
        
        self.callees_in_seed_apis = ''

        self.ignored_ops = open(ignored_ops_file,'r').read().split('\n')
        
        
    def __ignore_irrelvant_ops(self,callees):
        filtered_callees = [callee for callee in callees if callee not in self.ignored_ops and not callee.startswith('__')]
        return filtered_callees
    
    
    
    def get_predece(self):
        return self.__query_for_predece()
    
    
    
    def __query_for_predece(self):
        predece = None
        inferred_critical_var = ''
        
        if self.critical_var == 'retval':
            predece = self.__chain_arg_to_retval()
            inferred_critical_var = 'arg'
            if not predece:
                predece = self.__chain_retval_to_retval()
                inferred_critical_var = 'retval'
        if self.critical_var == 'arg':
            predece = self.__chain_retval_to_arg()
            inferred_critical_var = 'retval'
            if not predece:
                predece = self.__chain_arg_to_arg()
                inferred_critical_var = 'arg'
        
        
        predece = self.__ignore_irrelvant_ops(predece)
        
        if len(predece)>1 or not predece: 
            return None,None
        else:
            return predece[0],inferred_critical_var
                
    
        
    
    def __chain_arg_to_arg(self):
        query =  f'_ {self.seed_api}(_ *$var){{_($callee(_($var)));}}'
        callees = CodeSearcher("linux").weggli_get_desired_filed(query,'callee')
        return callees
    
    
    def __chain_retval_to_arg(self):
        query = f'{self.seed_api} ($var) {{$var = $callee();NOT: $var=$func();}}'
        callees = CodeSearcher("linux").weggli_get_desired_filed(query,'callee')
        return callees
    
    
    
    def __chain_arg_to_retval(self):
        query = f'{self.seed_api} () {{return $callee($var)}}'
        callees = CodeSearcher("linux").weggli_get_desired_filed(query,'callee')
        return callees
    
     
    def __chain_retval_to_retval(self):
        query = f'{self.seed_api} () {{$var = $callee();NOT: $var=$func();return $var;}}'
        callees = CodeSearcher("linux").weggli_get_desired_filed(query,'callee')
        return callees

    
