import sys
from utils.CodeSearcher import CodeSearcher

class PropogateChain:
    def __init__():
        pass
    
    @staticmethod
    def retval_to_retval_extender(target_API,repo_name):
        queries = [
            f'return {target_API}();',
            f'$ret={target_API}();return $func(_($ret));',
            f'$ret={target_API}();return _($ret);'
        ]
        succ_APIs = []
        for query in queries:
            succ_APIs += CodeSearcher(repo_name).weggli_get_found_func(query)
    
        return list(set(succ_APIs))

    @staticmethod
    def arg_to_retval_extender(target_API,repo_name):
        query = f'{target_API}(_($ret)); return $ret;'
        succ_APIs = CodeSearcher(repo_name).weggli_get_found_func(query)
        return succ_APIs


    @staticmethod
    def arg_to_arg_extender(target_API,repo_name):
        query = f'_ $func(_* $arg){{{target_API}(_($arg));}}'
        succ_APIs = CodeSearcher(repo_name).weggli_get_found_func(query)

        return succ_APIs


    @staticmethod
    def retval_to_arg_extender(target_API,repo_name):
        query = f'_ $func(_* $arg){{{target_API}(_($arg));}}'
        succ_APIs = CodeSearcher(repo_name).weggli_get_found_func(query)
        
        return succ_APIs