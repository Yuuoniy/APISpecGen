import pandas as pd
import os

def find_true_bugs_in_bug_reports(bug_reports_csv, true_bug_list_csv):
    bug_reports = pd.read_csv(bug_reports_csv)
    true_bug_list = pd.read_csv(true_bug_list_csv)

    print(f"The set of true bugs : {len(true_bug_list)}")

    bug_reports_set = set(
        zip(bug_reports['test_func'], bug_reports['main_api'], bug_reports['sec_op'])
    )
    true_bug_list_set = set(
        zip(true_bug_list['test_func'], true_bug_list['main_api'], true_bug_list['sec_op'])
    )

    # Find common bugs and those in true_bug_list that are not in bug_reports
    found_bugs = true_bug_list_set & bug_reports_set
    not_found_bugs = true_bug_list_set - bug_reports_set

    # Output the results
    print(f"Number of true bugs found in bug reports: {len(found_bugs)}")


if __name__ == '__main__':
    WORKDIR = '/root/APISpecGen'

    bug_reports = os.path.join(WORKDIR,'BugDetection/ReferenceData/bug_report.csv')
    true_bug_list = os.path.join(WORKDIR,'BugDetection/ReferenceData/true_bugs_provided_in_5.16.csv')

    find_true_bugs_in_bug_reports(bug_reports, true_bug_list)
