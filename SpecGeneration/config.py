import configparser
import pandas as pd
from icecream import ic
import click as cli
import os
from rich.progress import track
from datetime import datetime



cp = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
WORKDIR = "/root/APISpecGen"
CONFIG_PATH = f'{WORKDIR}/config.cfg'
cp.read(CONFIG_PATH)




SPEC_DATA_ROOT = cp.get('GENERATOR','spec')
SPEC_NUM_THREADS = int(cp.get('GENERATOR','num_threads')) 
TREE_SITTER_C = cp.get("TOOLS","tree-sitter-c")

if not os.path.exists(SPEC_DATA_ROOT):
    os.mkdir(SPEC_DATA_ROOT)