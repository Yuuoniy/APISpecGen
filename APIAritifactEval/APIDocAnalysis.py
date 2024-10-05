import json
import sys
import os

def read_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def check_api_in_doc(api_name, sec_op, api_docs):
    for api_doc in api_docs:
        if api_doc['name'] == api_name:
            info_fields = ['info', 'return_info', 'detail_info']
            any_info_non_empty = any(api_doc.get(field, '').strip() for field in info_fields)
            found_sec_op = any(sec_op in api_doc.get(field, '') for field in info_fields if api_doc.get(field, '').strip())
            return not any_info_non_empty, found_sec_op
    return True, False

def process_doc_info(spec_data, api_docs):
    updated_data = []
    for entry in spec_data:
        # if entry['hasUsage'] and entry['usageCount'] >= 1:
        is_doc_empty, found_sec_op = check_api_in_doc(entry['API'], entry['SecOp'], api_docs)
        entry['IsDocEmpty'] = is_doc_empty
        entry['SecOpInDoc'] = found_sec_op
        updated_data.append(entry)
    return updated_data

def calculate_statistics(spec_data):
    total_entries = len(spec_data)
    # total_entries = len([entry for entry in spec_data if entry['hasUsage'] and entry['usageCount'] >= 1])
    sec_op_not_in_doc = [entry for entry in spec_data if not entry.get('SecOpInDoc', True)]
    non_empty_docs = [entry for entry in spec_data if not entry.get('IsDocEmpty', True)]
    sec_op_not_in_non_empty_doc = [entry for entry in spec_data if not entry.get('SecOpInDoc', True) and not entry.get('IsDocEmpty', False)]
    
    if total_entries == 0:
        print("No valid usage entries found.")
        return

    sec_op_not_in_doc_count = len(sec_op_not_in_doc)
    sec_op_not_in_non_empty_doc_count = len(sec_op_not_in_non_empty_doc)

    sec_op_not_in_doc_ratio = sec_op_not_in_doc_count / total_entries
    sec_op_not_in_non_empty_doc_ratio = sec_op_not_in_non_empty_doc_count / len(non_empty_docs) if non_empty_docs else 0

    print(f"[API Doc Analysis]: {sec_op_not_in_doc_ratio:.2%} of Specs not mentioned in Doc For All APIs {sec_op_not_in_doc_count}/{total_entries}")
    print(f"[API Doc Analysis]: {sec_op_not_in_non_empty_doc_ratio:.2%} of Specs not mentioned in Doc for those API having docs: {sec_op_not_in_non_empty_doc_count}/{len(non_empty_docs)}")


def API_doc_analysis(usage_file, doc_file):
    usage_data = read_json(usage_file)
    api_docs = read_json(doc_file).get('api_doc', [])

    updated_data = process_doc_info(usage_data, api_docs)
    
    calculate_statistics(updated_data)



