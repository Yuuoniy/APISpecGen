from utils.CodeSearcher import CodeSearcher
from tqdm import tqdm
import concurrent.futures
import json
from config import SPEC_NUM_THREADS


class IsErrSpecPropogate:
    def __init__(self,repo_name,max_depth):
        self.explored_apis = []
        self.max_depth = max_depth
        self.repo_name = repo_name
        self.num_threads = SPEC_NUM_THREADS
        self.generated_specs = []

    def workflow(self):
        funcs = self.__get_return_value_is_err_func(self.repo_name)

        self.explored_apis.extend(funcs)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            list(tqdm(executor.map(self.iterative_propogation_analysis_thread, funcs), total=len(funcs)))

        return self.generated_specs
      
    def __get_return_value_is_err_func(self,repo_name):
        query = "_ $func(){return ERR_PTR();}"
        err_ptr_func = CodeSearcher(repo_name).weggli_get_found_func(query)
        return err_ptr_func
    

    def iterative_propogation_analysis_thread(self, func):
        self.analyze_spec(func, func, 1, API_path=[func], var_path=['retval'])
        self.iterative_propogation_analysis(func, current_depth=1, API_path=[func], var_path=['retval'])


    def iterative_propogation_analysis(self, func, current_depth, API_path, var_path):
        if current_depth > self.max_depth:
            return

        succs = self.__propogate_is_err_specs(func)
        for succ in succs:
            if succ not in self.explored_apis:
                self.explored_apis.append(succ)
                self.analyze_spec(func, succ, current_depth + 1, API_path + [succ], var_path + ['retval'])
                self.iterative_propogation_analysis(succ, current_depth + 1, API_path + [succ], var_path + ['retval'])                
                
    
    def analyze_spec(self, seed, succ, current_depth, API_path, var_path):
        has_usage,usage_count = self.__get_usage_and_count(succ)
        spec = {
            'API': succ,
            'SecOp': 'IS_ERR', 
            'usageCount': usage_count,
            'depth': current_depth,
            'API_path': '->'.join(API_path),
            'var_path': '->'.join(var_path)
        }
        self.generated_specs.append(spec)
        
    
    def __propogate_is_err_specs(self, func):
        succs = []
        query1 = f'NOT: return ERR_PTR(_); $ret = {func}(); NOT: $ret=_; return $ret; NOT: return ERR_PTR(_);'
        query2 = f'NOT: return ERR_PTR(_); return {func}(_); NOT: return ERR_PTR(_);'
        succs += CodeSearcher("linux").weggli_get_found_func(query1)
        succs += CodeSearcher("linux").weggli_get_found_func(query2)
        return succs

    def __get_usage_and_count(self,func):
        query1 = f'$ret={func}(); if(IS_ERR($ret)){{}};' 
        query2 = f'$ret={func}(); if(IS_ERR($ret))_; '
        usages = CodeSearcher("linux").weggli_get_found_func(query1)
        usages += CodeSearcher("linux").weggli_get_found_func(query2)
        return len(usages)!=0, len(usages)
    

if __name__ == "__main__":
    analyzer = IsErrSpecPropogate()
    analyzer.workflow()