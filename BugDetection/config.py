import configparser
import pandas as pd
from icecream import ic
import click as cli
import os
from rich.progress import track
from rich.console import Console


from datetime import datetime

console = Console()


cp = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
CONFIG_PATH = '/root/APISpecGen/config.cfg'
cp.read(CONFIG_PATH)


def time_format():
    return f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}|> '

ic.configureOutput(prefix=time_format,includeContext=True)

DATA_ROOT = cp.get('DETECTOR','data')
DETECTOR_DATA_ROOT = cp.get('DETECTOR','data')
DETECTOR_WORK_ROOT = cp.get('DETECTOR','work')
TREE_SITTER_C = cp.get("TOOLS","tree-sitter-c")
BUG_REPORT_FILE = cp.get('DETECTOR','bug_report')
CHK_BUG_REPORT_FILE = cp.get('DETECTOR','chk_bug_report')
DETECTOR_NUM_THREADS = int(cp.get('DETECTOR','num_threads'))

if not os.path.exists(DETECTOR_DATA_ROOT):
    os.mkdir(DETECTOR_DATA_ROOT)