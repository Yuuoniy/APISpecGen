import json
import os
from collections import Counter
from pathlib import Path


def get_common_subwords(input_spec_file, output_subwords_file='common_subwords.csv'):
    subword_counter = Counter()
    if not os.path.isfile(input_spec_file):
        print(f"File not found: {input_spec_file}")

    with open(input_spec_file, 'r') as infile:
        data = json.load(infile)

    unique_apis = set(entry['API'] for entry in data)
    
    for api in unique_apis:
        tokens = api.split('_')
        subword_counter.update(tokens)

    total_subwords = sum(subword_counter.values())
    common_subwords_list = [(subword, count, count / total_subwords * 100) for subword, count in subword_counter.most_common()]

    with open(output_subwords_file, 'w') as f:
        f.write('Subword,Count,Percentage\n')
        for subword, count, percentage in common_subwords_list:
            f.write(f'{subword},{count},{percentage:.2f}\n')

    return common_subwords_list


def analyze_the_util_API_name(subwords,input_file):
    subwords_set = set(subwords)

    total_apis_count = 0
    total_filtered_count = 0
    
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")

    with open(input_file, 'r') as infile:
        data = json.load(infile)

    unique_apis = set(entry['API'] for entry in data)

    filtered_apis = [api_name for api_name in unique_apis if not any(subword in api_name.split('_') for subword in subwords_set)]

    total_apis = len(unique_apis)
    filtered_count = len(filtered_apis)
    total_apis_count += total_apis
    total_filtered_count += filtered_count

    total_ratio = (total_filtered_count / total_apis_count) * 100 if total_apis_count > 0 else 0
    print(f"[API Name Analysis]:{total_ratio:.2f}% APIs do not contain the informative subwords (verbs) ({total_filtered_count} out of {total_apis_count}).")