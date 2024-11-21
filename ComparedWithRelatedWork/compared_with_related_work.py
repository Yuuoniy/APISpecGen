import csv
import pandas as pd

def compare_work(spec_file, tool_file, bugs_file, tool_name):
    spec_df = pd.read_csv(spec_file)
    tool_df = pd.read_csv(tool_file, header=None, names=["main_api", "sec_op"])
    bugs_df = pd.read_csv(bugs_file)

    spec_pairs = set(zip(spec_df["main_api"].str.strip(), spec_df["sec_op"].str.strip()))
    tool_pairs = set(zip(tool_df["main_api"].str.strip(), tool_df["sec_op"].str.strip()))
    
    bugs_pairs = bugs_df[["main_api", "sec_op", "test_func"]]
    
    covered_spec_pairs = tool_pairs & spec_pairs
    spec_coverage = len(covered_spec_pairs) / len(spec_pairs) if spec_pairs else 0
    
    bugs_covered = bugs_pairs[
        bugs_pairs.apply(lambda row: (row["main_api"], row["sec_op"]) in tool_pairs, axis=1)
    ]
    bug_coverage = len(bugs_covered) / len(bugs_pairs) if not bugs_pairs.empty else 0
    
    return {
        "Tool": tool_name,
        "Spec Coverage": f"{int(spec_coverage * 100)}%", 
        "Bug Coverage": f"{int(bug_coverage * 100)}%", 
    }


def check_ippo_coverage(ippo_file, apispecgen_bugs_file):
    apispecgen_bugs = pd.read_csv(apispecgen_bugs_file)
    
    # IPPO bug report format: buggyfunc,releaseFunc (test_func,sec_op)
    apispecgen_strings = apispecgen_bugs.apply(
        lambda row: f"{row['test_func']},{row['sec_op']}", axis=1
    ).tolist()

    # 加载 IPPO 的 bug reports
    with open(ippo_file, "r") as f:
        ippo_content = f.read()


    covered_strings = [
        pair for pair in apispecgen_strings if pair in ippo_content
    ]

    coverage_rate = len(covered_strings) / len(apispecgen_strings) if apispecgen_strings else 0

    return {
        "Tool": 'IPPO',
        "Spec Coverage":'-',
        "Bug Coverage": f"{int(coverage_rate * 100)}%",  # 百分比格式
    }
    
    
def main():
    file_paths = {
        "APISpecGen_spec_file": "BugDetection/ReferenceData/SpecRelatedToBug.csv",
        "detected_bugs_file": "BugDetection/ReferenceData/true_bugs_provided_in_5.16.csv",
        "APHP_file": "ComparedWithRelatedWork/RelatedWorkData/APHP_Linux_Pairs",
        "Advance_file": "ComparedWithRelatedWork/RelatedWorkData/Advance_Linux_Pairs",
        "SinkFinder_file": "ComparedWithRelatedWork/RelatedWorkData/SinkFinder_Linux_Pairs",
        "IPPO_bug_results": "ComparedWithRelatedWork/RelatedWorkData/IPPO_results",
    }


    tools = [
        {"name": "APHP", "file": file_paths["APHP_file"]},
        {"name": "Advance", "file": file_paths["Advance_file"]},
        {"name": "SinkFinder", "file": file_paths["SinkFinder_file"]},
    ]
    
    results = [
        compare_work(file_paths["APISpecGen_spec_file"], tool["file"], file_paths["detected_bugs_file"], tool["name"])
        for tool in tools
    ]
    results.append(check_ippo_coverage(file_paths["IPPO_bug_results"], file_paths["detected_bugs_file"]))

    results_df = pd.DataFrame(results)
    print("Compared with Related Work")
    print(results_df.to_markdown(index=False))

if __name__ == "__main__":
    main()
