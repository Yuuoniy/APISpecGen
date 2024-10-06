import pandas as pd
import click
from datetime import datetime
from icecream import ic
import traceback
import os



class BugReportRanker:
    def __init__(self,report_file):
       
        columns=['repo_name','test_func','main_api','sec_op','var_type','var','scope','violated_path_num']
        self.origin_report = pd.read_csv(report_file,usecols=columns)
        self.report_dir = os.path.dirname(report_file)
        self.report_file = report_file
        ic('read from',report_file)
        self.repo_report_cluster_by_api = []
        # drop duplicate
        self.origin_report.drop_duplicates(keep='first', inplace=True)
        self.repo_names = self.origin_report['repo_name'].unique()
        
        
    def workflow(self):
        # perform analysis for each repo
        for repo_name in self.repo_names:
            repo_report = self.analyze_repo(repo_name)
            ic(f'{repo_name} report number:{len(repo_report)}')

            save_file = self.report_file.replace('.csv','_ranked.csv')
            repo_report.to_csv(save_file,index=False)
            # print saved file
            ic('save to ', save_file)
            
    
    
    def analyze_repo(self, repo_name):
        repo_report = self.origin_report[self.origin_report['repo_name'] == repo_name]
        # count by api
        self.repo_report_cluster_by_api = repo_report.groupby(by=['main_api']).size().to_frame(name='count').sort_values('count',ascending=False)
        # calcuate score for each bug report
        self.repo_report_cluster_by_api.reset_index(inplace=True)
        
        repo_report['score'] = repo_report.apply(self.get_score, axis=1)
        repo_report = repo_report.sort_values('score',ascending=False)
        
        return repo_report
    
    def get_score(self,report):
        try:
            count = self.repo_report_cluster_by_api[self.repo_report_cluster_by_api['main_api']==report['main_api']]['count']
            return ReportScorer(report,count).cal_score()
        except Exception as e:
            traceback.print_exc()
            return 0

class ReportScorer:
    '''
    count: how many reports are caused by the same api misuse
    '''
    def __init__(self, report, count):
        self.report = report
        self.count = int(count)
        self.score = 0
        self.scope_weight = {'Global': 1, 'Para': 2, 'Local': 100}
        
    def cal_score(self):
        try:
        # get score for each report
        # - Inter-analysis: count - Intra-analysis: scope, violated_path_num, 
            weights = [50,0.4,0.2]
            # give weight for different metrics 
            self.score = weights[0] * self.cal_count_score() + weights[1] * self.cal_scope_score() + weights[2] * self.cal_path_score()
            self.score = round(self.score,2)
            return self.score
        except Exception as e:
            traceback.print_exc()
            return 0
        
        
    def cal_count_score(self):
        # print(self.report,self.count)
        return 1 / self.count
    
    def cal_scope_score(self):
        return self.scope_weight[self.report['scope']]
    
    def cal_path_score(self):
        return int(self.report['violated_path_num'])


@click.command()
@click.option('--file', help='bug report file')
def report_rank(file):
    ranker = BugReportRanker(file)
    ranker.workflow() 
    
if __name__ == '__main__':
    report_rank()