
from statistics import mean
import json


def calculate_usage_stats(spec_file):
    with open(spec_file, 'r') as file:
            data = json.load(file)
            
    usage_counts = [entry['usageCount'] for entry in data if entry['hasUsage'] and entry['usageCount'] >= 1]

    if not usage_counts:
        return None, None, None

    avg_usage_count = mean(usage_counts)
    count_le_5 = sum(1 for count in usage_counts if count <= 5)
    count_le_10 = sum(1 for count in usage_counts if count <= 10)

    ratio_le_5 = count_le_5 / len(usage_counts)
    ratio_le_10 = count_le_10 / len(usage_counts)

    print(f"[API Usage Analysis]: {ratio_le_10:.2%} API pairs usage occur less than 10 times, {ratio_le_5:.2%} API pairs usage occur less than 5 times.")
    return avg_usage_count, (count_le_5, ratio_le_5), (count_le_10, ratio_le_10)