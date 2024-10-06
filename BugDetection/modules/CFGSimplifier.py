import code
import re
import traceback
import networkx as nx
import pygraphviz
from networkx.drawing import nx_agraph
import os
from rich.progress import track
import icecream as ic
import sys
from rich import print
from multiprocessing import Pool
from multiprocessing import cpu_count
from rich.console import Console
from config import DETECTOR_DATA_ROOT
from utils import cfg_analyzer

console = Console()

from utils.tree_sitter_helper import *



import timeout_decorator
import logging

logger = logging.getLogger('detector')


ret_labels = ['(METHOD_RETURN,','(RETURN,']
class CFGSimplifier:
    
    methods = []
    funcs_cfg =['(METHOD_RETURN,','(METHOD,' ,'(RETURN,',] 
    critical_variable = ''
    critical_variable_alias = []
    VarScope = False
    source = ''
    func_def = ''
    parser = tree_sitter_init()

    def __init__(self,rule):
        self.main_api = rule['main_api']
        self.var_type = rule['var_type']
        self.repo_name = rule['repo_name']
        self.REPO_DATA_ROOT = os.path.join(DETECTOR_DATA_ROOT,self.repo_name)
        
        
    
    def simplify_CFG(self,test_func):
        ic()
        self.test_analysis_cfg_for_one_func(test_func)
        
        return self.critical_variable,self.VarScope


    def check_variable_scope(self):
        self.VarScope  =  cfg_analyzer.get_var_scope(self.func_def,self.critical_variable)
               
                
                
    def get_alias(self,G):
        # direct alias
        exprs = cfg_analyzer.get_assignment_use_var_as_right_value(G,self.critical_variable)
        left_alias = cfg_analyzer.get_left_vals_in_assignment_exprs(exprs)
        self.critical_variable_alias = left_alias+[self.critical_variable]

        # indirect alias, struct related hdmi->cec_dev = &cec_pdev->dev;
        exprs = cfg_analyzer.get_assignment_use_var_as_struct_of_right_value(G,self.critical_variable)
        left_alias_struct = cfg_analyzer.get_left_vals_in_assignment_exprs(exprs)
        self.critical_variable_alias += left_alias_struct

        if self.critical_variable.startswith("**"):
            self.critical_variable_alias.append(self.critical_variable[2:])
        elif self.critical_variable.startswith("*"):
            self.critical_variable_alias.append(self.critical_variable[1:])
        # check if the critical variable has the format : saif_np[0]->saif_np
        # pdb.set_trace()
        if match := re.match(r'(\w+)\[\d+\]', self.critical_variable):
            self.critical_variable_alias.append(match.group(1))

    
    @timeout_decorator.timeout(500)
    def test_analysis_cfg_for_one_func(self,test_func,out_dir=None,code_file=None):
        
        if out_dir is None:
            out_dir = f'{self.REPO_DATA_ROOT}/{self.main_api}'
        
        try:
            # ic(test_func)
            
            G = nx.drawing.nx_agraph.read_dot(f'{out_dir}/cfg-outdir/{test_func}.dot')
            # ic(f'{out_dir}/cfg-outdir/{test_func}.dot')
            if code_file is None:
                code_file = f"{out_dir}/def/{G.name}.c"
            # G = nx.drawing.nx_agraph.read_dot(f'{dir}/cfg-outdir/{test_func}.dot')
            self.funcs_cfg =['(METHOD_RETURN,','(METHOD,' ,'(RETURN,',] 
            
            
            func_def = open(code_file).read()
            self.methods = cfg_analyzer.get_func_call(func_def)
            self.funcs_cfg.extend([f"({x}," for x in self.methods]) # FIXME, why (???
            # ic(f'G.name: {out_dir}/cfg-outdir/{test_func}.dot')
            self.get_path_by_node(G,self.main_api,func_def,out_dir)
            self.func_def = func_def
            # pdb.set_trace()
            
        except Exception as e:
            ic(f"{test_func} {e}")
            # logger.error(f"{test_func} {e}")
            # console.print_exception(show_locals=True)
            
        self.check_variable_scope()
        if self.critical_variable.startswith("*"):
            self.critical_variable = self.critical_variable[1:]
        return self.critical_variable,self.VarScope,self.func_def




    def get_path_by_node(self,G,func,func_def,dir=None,regenerate=True):
        # sourcery skip: avoid-builtin-shadow
        # global critical_variable,source
        # source = node_id_by_label(G,func)
        if dir is None:
            dir = f'{self.REPO_DATA_ROOT}/{self.main_api}'

        try:
            self.source,source_code = cfg_analyzer.assignement_node_id_by_label(G,func)
            # pdb.set_trace()
            if self.source is None:
                self.source,source_code = cfg_analyzer.callsite_node_id_by_label(G,func)

            # get assignemt
            if self.var_type == 'retval':
                try:
                    self.critical_variable = cfg_analyzer.get_assignment_left_variable(source_code)
                except Exception:
                    # ic("[error] fail to get assginement variable, may be var_type is not retval",self.main_api)
                    logger.error(f"[error] fail to get assginement variable, may be var_type is not retval {self.main_api}, {func}, {source_code}")
            else:
                self.critical_variable = cfg_analyzer.get_pos_arg_var(self.var_type,source_code)
                # self.critical_variable = cfg_analyzer.get_first_arg_var(source_code)

            self.get_alias(G)
            # ic(self.critical_variable,self.critical_variable_alias)
            '''
            if not cfg_analyzer.check_variable_is_local(func_def,self.critical_variable):
                return
            '''
            # avoid generate ASG twice
            simple_cfg_file = f"{dir}/simple_cfg/{G.name}-{self.main_api}.dot"
            if os.path.exists(simple_cfg_file) and not regenerate:
                return
            target = cfg_analyzer.node_id_by_label(G,'METHOD_RETURN')
            # ic(self.source,target)
            G_func = nx.DiGraph()
            for path in list(nx.all_simple_paths(G, source=self.source, target=target)):
            # for path in track(list(nx.all_simple_paths(G, source=self.source, target=target))):
                valid_paths,valid_labels = self.get_simple_path(G,path)
                path_edges = list(zip(valid_paths,valid_paths[1:]))
                # print(valid_paths,valid_labels) # need unique path.
                G_func.add_edges_from(path_edges)
            for node in G_func.nodes:
                G_func.nodes[node]['label'] = G.nodes[node]['label']
            #TODO remove loop
            G_func.remove_edges_from(nx.selfloop_edges(G_func))
            nx_agraph.write_dot(G_func,f"{dir}/simple_cfg/{G.name}-{self.main_api}.dot")
                # print(f"saved to : {dir}/simple_cfg/{G.name}-{self.main_api}.dot")
        except Exception as e:
            # ic(f"{G.name} {e}")
            logger.error(f"{self.main_api} {G.name} {e}")
            # console.print_exception(show_locals=True)
            return
    
    def remove_self_cycle(self,G):
        G.remove_edges_from(nx.selfloop_edges(G))
        
    
    def get_simple_path(self,G,path):  # sourcery skip: low-code-quality
        
        valid_paths = []
        valid_labels = []
        labels = nx.get_node_attributes(G, "label")
        # print(labels)
        
        # add source node.
        
        for idx,node in enumerate(path):
            
            # print(funcs_cfg)
            # print label in the path
            # print(labels[node])
            if path[idx] == self.source:
                valid_paths.append(path[idx]) # id
                valid_labels.append(labels[path[idx]][:-1].split(',',1)[1]) # statement
            # pdb.set_trace()
            if any(func in labels[node] for func in self.funcs_cfg):
                # assignment the return value of function.
                # pdb.set_trace()
                for critical_var in self.critical_variable_alias: # consider critical variable and alias.
                    # pdb.set_trace()
                    if idx+1 < len(path) and  '<operator>.assignment' in labels[path[idx+1]] \
                        and labels[node][1:-1].split(',',1)[0] in labels[path[idx+1]].split(',',1)[1]: # funcname in the assgiment
                        label = labels[path[idx+1]][:-1].split(',',1)[1]
                        # except assignmet for the critical variables
                        # ic(label,critical_var)
                        try:
                            if cfg_analyzer.get_assignment_left_variable(labels[path[idx+1]].split(',',1)[1][:-1])==critical_var:
                                # valid_paths.append(path[path[idx+1]]) # id
                                valid_paths.append(path[-1]) # id
                                valid_labels.append(label) # statement
                                return valid_paths,valid_labels # FIXME, why return here?
                        except Exception:
                            pass
                            # print("error")
                            
                        if self.dependency_on_critical_variable(label,critical_var) or any(ret in labels[node] for ret in ret_labels):
                            valid_paths.append(path[idx+1]) # id
                            valid_labels.append(label) # statement
                    else:
                        label = labels[node][:-1].split(',',1)[1]
                        # pdb.set_trace()
                        if self.dependency_on_critical_variable(label,critical_var) or any(ret in labels[node] for ret in ret_labels):
                            valid_paths.append(node)
                            valid_labels.append(label)
                        # ic(label)
            # if is a branch statement, outdegree larger than 1
            if G.out_degree(node) > 1:
                label = labels[node][:-1].split(',',1)[1]
                valid_paths.append(node)
                valid_labels.append(label)



        if not self.check_if_has_op_on_critical_variables(valid_labels):
            return '',[]
        return valid_paths,valid_labels

    def check_if_has_op_on_critical_variables(self,valid_paths):
        for label in valid_paths[:]:
        # for label in valid_paths[1:]:
            for var in self.critical_variable_alias:
                if self.dependency_on_critical_variable(label,var):
                    return True
        return False
        

    def dependency_on_critical_variable(self,slice,critical_var):
        # pdb.set_trace()
        
        if not slice.endswith(';'):
            slice += ';'
        # struct style, only consider the struct.
        if "->" in critical_var:
            critical_var = critical_var.split('->')[0]
        tree = self.parser.parse(bytes(slice, "utf8"))
        idents = find_node_by_type(tree, "identifier")
        ident_codes = [get_node_content(x,slice) for x in idents]
        return critical_var in ident_codes

    # current consider return value of function call operation


