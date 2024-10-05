import os
import json
import pandas as pd
from config import SPEC_DATA_ROOT,WORKDIR

def count_generated_specs(api_list, directory,depth):
    data = []
    total_count = 0  
    
    for api in api_list:
        file_name = f'linux_{api}_{depth}_generated_specs.json'
        file_path = os.path.join(directory, file_name)

        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                try:
                    items = json.load(file)
                    item_count = len(items)
                    total_count += item_count  
                    data.append({'API': api,'Specs Count': item_count})
                except json.JSONDecodeError:
                    print(f"Error reading JSON from {file_path}. Skipping...")
        else:
            print(f"File {file_path} does not exist. Skipping...")

    df = pd.DataFrame(data)

    print("\nAPI Spec Count Summary:")
    print(df.to_string(index=False))
    print(f"\nTotal Specs: {total_count}")

import sys

if __name__ == "__main__":
    depth = 10
    seed_apis = ['get_device', 'device_initialize','try_module_get', 'kmalloc','kstrdup',  'ERR_PTR']
    
    # get use_referenced_data from command line
    # the default value is False
    
    use_generated_data = False
    if len(sys.argv) > 1:
        use_generated_data = sys.argv[1] == 'True'
    
    generated_dir = SPEC_DATA_ROOT
    reference_dir = os.path.join(WORKDIR, 'SpecGeneration/Data/ReferenceData')
    
    data_dir = generated_dir if use_generated_data else reference_dir
    
    count_generated_specs(seed_apis, data_dir, depth)
