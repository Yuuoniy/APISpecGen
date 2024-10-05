import json
from QuickMode.SpecPropogateAnalyzer import SpecPropogateAnalyzer
from QuickMode.Spec import APISpec
from QuickMode.IsErrSpecPropogate import IsErrSpecPropogate
import json
import argparse
import configparser
import os
from config import SPEC_DATA_ROOT,SPEC_NUM_THREADS



def quick_mode_for_checked_spec(seedSpec,repo_name,max_depth):
    analyzer = IsErrSpecPropogate(repo_name,max_depth)
    generated_specs = analyzer.workflow()
    return generated_specs


def quick_mode_for_paired_spec(seedSpec,repo_name, max_depth):
    analyzer = SpecPropogateAnalyzer(repo_name,max_depth)
    generated_specs = analyzer.bidirectional_propogation_analysis(seedSpec)
    return generated_specs




def filter_specs_by_usage(generated_specs):
    filtered_specs = [entry for entry in generated_specs if not entry['var_path'].split('->')[-1] == 'arg']
    filtered_specs = [entry for entry in filtered_specs if entry.get('hasUsage', False)]
    
    # depuplicate
    filtered_specs = [dict(t) for t in {tuple(d.items()) for d in filtered_specs}]
    
    return filtered_specs



def main(seedAPI, SeedSecOp, critical_var, repo_name, max_depth):
    seedSpec = APISpec(seedAPI, SeedSecOp, critical_var)
    if seedAPI=='ERR_PTR':
        generated_specs = quick_mode_for_checked_spec(seedSpec, repo_name, max_depth)
    else:
        generated_specs = quick_mode_for_paired_spec(seedSpec, repo_name, max_depth)
    
    generated_specs = filter_specs_by_usage(generated_specs)
    
    outfile = os.path.join(SPEC_DATA_ROOT,f'{repo_name}_{seedAPI}_{max_depth}_generated_specs.json') 
    
    
    with open(outfile, 'w') as f:
        json.dump(generated_specs, f)
    
    print(f"Generated Specifcations written to {outfile}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process API Specifications and generate output.')

    parser.add_argument('--seedAPI', type=str, required=True, help='The initial seed API to use')
    parser.add_argument('--seedSecOp', type=str, required=True, help='The second operation associated with the seed API')
    parser.add_argument('--critical_var', type=str, required=True, help='The critical variable in the operation')
    parser.add_argument('--repo_name', type=str, default='kernel', help='The repository name')
    parser.add_argument('--max_depth', type=int, default=10, help='Maximum depth for search (default: 10)')

    args = parser.parse_args()

    main(args.seedAPI, args.seedSecOp, args.critical_var, args.repo_name, args.max_depth)
        
        

