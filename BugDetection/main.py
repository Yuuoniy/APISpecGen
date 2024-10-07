from modules.preprocess import Preprocess
import pandas as pd
import os
import json
from modules.Runner import Runner,ChkRunner
import click
import logging
import sys
from config import DATA_ROOT,ic,DETECTOR_NUM_THREADS
import time
import traceback
from tqdm import tqdm
import concurrent.futures


detect_name =  time.strftime("%m-%d", time.localtime()) + '_detector.log'

logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s',filename=os.path.join(DATA_ROOT,detect_name),level=logging.DEBUG)
logger = logging.getLogger('detector')
logger.setLevel(logging.DEBUG)
logger.name = 'detector'

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    click.echo(f"Debug mode is {'on' if debug else 'off'}")


@cli.command("paired_spec_test")
@click.option('--spec_path')
def paired_spec_test(spec_path):
    try:
        if spec_path.endswith('.json'):
            pairs = json.load(open(spec_path))
        elif spec_path.endswith('.csv'):
            pairs = pd.read_csv(spec_path)
            pairs = pairs.to_dict('records')
            
        for pair in pairs:
            spec = pair
            spec['repo_name'] = 'kernel'
            spec['main_api'] = spec['API']
            spec['sec_op'] = spec['SecOp']
            spec['var_type'] = spec['var_role']
            spec['api_status'] = 'success'
            spec['path_type'] = 'error'
            
            ic(spec)
            runner = Runner(spec)
            runner.bug_detect_runner_batch()
    except Exception as e:
        traceback.print_exc()
        ic(e)
        logger.error(e)
        return False
    
@cli.command("checked_spec_test")
@click.option('--spec_path')
def checked_spec_test(spec_path):
    try:
        if spec_path.endswith('.json'):
            specs = json.load(open(spec_path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=DETECTOR_NUM_THREADS) as executor:
            futures = []

            for spec in specs:
                spec['repo_name'] = 'kernel'
                futures.append(executor.submit(run_chk_runner, spec))
                

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result() 
                except Exception as e:
                    traceback.print_exc()
                    ic(e)
                    logger.error(e)
                    return False
    except Exception as e:
        traceback.print_exc()
        ic(e)
        logger.error(e)
        return False

def run_chk_runner(spec):
    try:
        chk_runner = ChkRunner(spec)
        chk_runner.runner()
    except Exception as e:
        traceback.print_exc()
        ic(e)
        logger.error(e)

if __name__ == '__main__':
    ic(DATA_ROOT)
    if not os.path.exists(DATA_ROOT):
        os.mkdir(DATA_ROOT)
    
    cli()
