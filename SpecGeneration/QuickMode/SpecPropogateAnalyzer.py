from QuickMode.PropogateChain import PropogateChain
from QuickMode.SpecGenerator import SpecGenerator
from QuickMode.SpecPropogatePre import SpecPropogatePre
import concurrent.futures
from tqdm import tqdm
from config import SPEC_NUM_THREADS
from QuickMode.Spec import APISpec


class SpecPropogateAnalyzer:
    def __init__(self,repo_name,max_depth):
        self.repo_name = repo_name
        self.max_depth = max_depth
        self.interesting_keywords = []
        self.keywords = ['get', 'find', 'alloc', 'lookup'] 
        self.num_threads = SPEC_NUM_THREADS 
        self.explore_API = []
        self.explore_specs = []
        

    
    def bidirectional_propogation_analysis(self, seedSpec):
        generated_specs = []
        generated_specs = self.iterative_propogation_analysis_for_successors(seedSpec,1)
        generated_specs += self.iterative_propogation_analysis_for_predecessor(seedSpec,1)
        return generated_specs
    
    
    def iterative_propogation_analysis_for_predecessor(self, seedSpec, current_depth, API_propa_path=None, critical_var_propa_path=None):
        if current_depth > self.max_depth:
            return []
        
        pre_API,inferred_critical_var = SpecPropogatePre(seedSpec).get_predece()
        if pre_API is None or pre_API in self.explore_API:  # Check if pre_API already explored
            return []
            
        # generate the specifcation for the predecessor
        spec_generator = SpecGenerator()
        sec_op, count = spec_generator.infer_postOp_for_inferred_API(inferred_API=pre_API, seedSecOp=seedSpec.secOp, inferred_critical_var=inferred_critical_var,repo_name=self.repo_name,propo_direction='pre')
        
        has_usage = sec_op is not None
        sec_op = sec_op

        current_API_path = (API_propa_path or [seedSpec.API]) + [pre_API]
        current_var_path = (critical_var_propa_path or [seedSpec.critical_var]) + [inferred_critical_var]
        
        if not has_usage:
            return []
        

        generated_specs = [{
            'API': pre_API,
            'SecOp': sec_op,
            'hasUsage': has_usage,
            'usageCount': count,
            'depth': current_depth,
            'API_path': '->'.join(current_API_path),
            'var_path': '->'.join(current_var_path)
            }]
        
        

        Generated_spec_for_pre = APISpec(pre_API, sec_op, inferred_critical_var)     
        # self.explore_specs.append((pre_API, inferred_critical_var))
        
        # successors analysis for the predecessor
        generated_specs += self.iterative_propogation_analysis_for_successors(Generated_spec_for_pre, current_depth + 1, current_API_path, current_var_path)
        
        # iterative predecessor analysis
        generated_specs += self.iterative_propogation_analysis_for_predecessor(Generated_spec_for_pre,current_depth + 1,current_API_path,current_var_path)

        return generated_specs  
        
    
    
    def iterative_propogation_analysis_for_successors(self, seedSpec, current_depth, API_propa_path=None, critical_var_propa_path=None):
        if current_depth > self.max_depth:
            return []


        if (seedSpec.API, seedSpec.critical_var) in self.explore_specs:
            return []
        
        self.explore_specs.append((seedSpec.API, seedSpec.critical_var))
        
        API_propa_path = API_propa_path or [seedSpec.API]
        critical_var_propa_path = critical_var_propa_path or [seedSpec.critical_var]
        
        succs_via_retval, succs_via_arg = self.propogation_analysis_for_successors(seedSpec.API, seedSpec.critical_var)
        propogation_types = ['retval', 'arg']
        
        generated_specs = []

        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for direction, inferred_apis in zip(propogation_types, [succs_via_retval, succs_via_arg]):
                if len(inferred_apis) == 0:
                    continue
                for inferred_API in tqdm(inferred_apis):
                    if inferred_API in ['main'] or 'devm' in inferred_API:
                        continue
                    if (inferred_API, direction) in self.explore_specs:
                        continue

                    
                    futures.append(executor.submit(self.analyze_wrapper, inferred_API, seedSpec.secOp, direction, current_depth, API_propa_path, critical_var_propa_path))

            for future in concurrent.futures.as_completed(futures):
                generated_specs.extend(future.result())
    
        return generated_specs
        
    
    def analyze_wrapper(self, wrapper, seed_secop, direction, current_depth, API_propa_path, critical_var_propa_path):
        spec_generator = SpecGenerator()
        sec_op, count = spec_generator.infer_postOp_for_inferred_API(inferred_API=wrapper, seedSecOp=seed_secop, inferred_critical_var=direction,repo_name=self.repo_name,propo_direction='succ')

        has_usage = sec_op is not None
        sec_op = sec_op or seed_secop

        current_API_path = API_propa_path + [wrapper]
        current_var_path = critical_var_propa_path + [direction]

        if has_usage or any(keyword in wrapper for keyword in self.keywords):
            generated_specs = [{
            'API': wrapper,
            'SecOp': sec_op,
            'hasUsage': has_usage,
            'usageCount': count,
            'depth': current_depth,
            'API_path': '->'.join(current_API_path),
            'var_path': '->'.join(current_var_path)
            }]
            
            generated_spec = APISpec(wrapper, seed_secop, direction)
            generated_specs += self.iterative_propogation_analysis_for_successors(generated_spec, current_depth + 1, current_API_path, current_var_path)
        else:
            generated_specs = []
            
        return generated_specs



    def propogation_analysis_for_successors(self,seed_api, ciritical_var):
        succ_via_retval = []
        succ_via_arg = []
        
        # the following contain four type edges propogating the critical variable.
        if ciritical_var == 'arg':
            succ_via_retval = PropogateChain.arg_to_retval_extender(seed_api,self.repo_name)
            succ_via_arg = PropogateChain.arg_to_arg_extender(seed_api,self.repo_name)
        elif ciritical_var == 'retval':
            succ_via_retval = PropogateChain.retval_to_retval_extender(seed_api,self.repo_name)
            succ_via_arg = PropogateChain.retval_to_arg_extender(seed_api,self.repo_name)
        else:
            raise ValueError(f"Unexpected var_path value: {ciritical_var}")

        return succ_via_retval, succ_via_arg
    