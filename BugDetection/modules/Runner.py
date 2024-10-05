import networkx as nx
from networkx.drawing import nx_agraph
from modules.preprocess import Preprocess,PreprocessSingleFunc
import os
from rich.progress import track
import icecream as ic
import sys
from multiprocessing import Pool
from datetime import datetime
import time
import timeout_decorator
import pdb
from modules.rules_checker import RuleCheckerSingle,chkCheckerSingle
from modules.CFGSimplifier import CFGSimplifier
import logging
from config import DETECTOR_DATA_ROOT,DETECTOR_NUM_THREADS

logger = logging.getLogger('detector')

class Runner:
    methods = []
    funcs_cfg =['(METHOD_RETURN,','(METHOD,' ,'(RETURN,',] 

    def __init__(self, rule,repo_name='',version=''):
        self.repo_name = rule['repo_name']
        self.version = version
        self.rule = rule
        self.CFGsimplifier = CFGSimplifier(rule)
        self.REPO_DATA_ROOT = os.path.join(DETECTOR_DATA_ROOT,self.repo_name)
        
                                               

    def bug_detect_runner_batch(self,dir=None):  # sourcery skip: avoid-builtin-shadow

        if not os.path.exists(self.REPO_DATA_ROOT):
            os.mkdir(self.REPO_DATA_ROOT)
        
        try:
            self.preprocess()
        except Exception as e:
            ic(e)

        if dir is None:
            dir = f'{self.REPO_DATA_ROOT}/{self.rule["main_api"]}'

        dot_files = os.listdir(f'{dir}/cfg-outdir')
        dot_files = [x for x in dot_files if x.endswith('.dot')]
        funcs = open(f'{dir}/caller_of_{self.rule["main_api"]}.txt','r').read().split('\n')
        
        logger.info(f'bug_detect_runner_batch: {self.rule["main_api"]} : {len(funcs)}')
        p = Pool(processes=DETECTOR_NUM_THREADS)
        for dot_file in dot_files:
        # for dot_file in track(dot_files):
            if dot_file.split(".")[0] not in funcs:
                continue
            p.apply_async(self.runner_one,(dot_file.split(".")[0],))
        p.close()
        p.join()
        

    def runner_one(self, test_func) -> bool:
        try:
            # print(f'runner_one: {test_func}')
            critical_var,varScope,func_def = self.CFGsimplifier.test_analysis_cfg_for_one_func(test_func)
            self.ruleChecker = RuleCheckerSingle(self.rule, critical_var, varScope,func_def)
            return self.ruleChecker.check_security_operations_for_func(test_func, critical_var)
        except Exception as e:
            print(e)
            
    def preprocess(self):
        Preprocess(self.repo_name,self.rule['main_api'])
        

    def preprocess_one(self,test_func):
        main_api = self.rule['main_api']
        if os.path.exists(f'{self.REPO_DATA_ROOT}/{self.rule["main_api"]}/simple_cfg/{test_func}-{main_api}.dot'):
            return
        ic("preprocess_one",test_func)
        PreprocessSingleFunc(self.repo_name, self.rule['main_api'],test_func)
        
    
    
class ChkRunner:
    def __init__(self,rule,repo_name=''):
        self.repo_name = rule['repo_name']
        self.rule = rule
        
    def runner(self):
        self.chkchecker = chkCheckerSingle(self.rule)
        self.chkchecker.check()