import os
import json
import pandas as pd
from config import SPEC_DATA_ROOT

def count_items_in_files(api_list, directory):
    data = []
    total_count = 0  
    
    for api in api_list:
        # file_name = f'Filter_{api}.json'
        file_name = f'linux_{api}_10_generated_specs.json'
        file_path = os.path.join(directory, file_name)

        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                try:
                    items = json.load(file)
                    item_count = len(items)
                    total_count += item_count  
                    data.append({'API': api,'Item Count': item_count})
                except json.JSONDecodeError:
                    print(f"Error reading JSON from {file_path}. Skipping...")
        else:
            print(f"File {file_path} does not exist. Skipping...")

    df = pd.DataFrame(data)

    print("\nAPI Item Count Summary:")
    print(df.to_string(index=False))
    print(f"\nTotal Item: {total_count}")

if __name__ == "__main__":
    api_list = ['get_device', 'kstrdup', 'device_initialize', 'kmalloc', 'try_module_get','ERR_PTR']


    directory = SPEC_DATA_ROOT
    # directory = '/root/APISpecGen/SpecGeneration/Data/Filtered'

    count_items_in_files(api_list, directory)
