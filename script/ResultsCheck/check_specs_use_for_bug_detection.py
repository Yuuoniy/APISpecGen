import json
import pandas as pd

def compare_specs(generated_specs_json, bug_related_specs_csv):
    with open(generated_specs_json, 'r') as json_file:
        generated_specs = json.load(json_file)

    bug_related_specs = pd.read_csv(bug_related_specs_csv)

    generated_api_secop = [(spec['API'], spec['SecOp']) for spec in generated_specs]

    found_specs = []
    not_found_specs = []

    for index, row in bug_related_specs.iterrows():
        main_api = row['main_api']
        sec_op = row['sec_op']
        if (main_api, sec_op) in generated_api_secop:
            found_specs.append(row)
        else:
            not_found_specs.append(row)

    print(len(not_found_specs))
    for spec in not_found_specs:
        print(spec['main_api'], spec['sec_op'])
        

import os

if __name__ == '__main__':
    WORKDIR = '/root/APISpecGen'
    spec_related_to_bugs = os.path.join(WORKDIR,'BugDetection/ReferenceData/SpecRelatedToBug.csv')
    generated_specs = os.path.join(WORKDIR,'/SpecGeneration/Data/ReferenceData/All_generated_specs.json')
    compare_specs(generated_specs, spec_related_to_bugs)
