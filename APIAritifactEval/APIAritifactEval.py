
from APINameAnalysis import analyze_the_util_API_name
from APIUsageAnalysis import calculate_usage_stats
from APIDocAnalysis import API_doc_analysis
import os
import configparser


cp = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
WORKDIR = "/root/APISpecGen"
CONFIG_PATH = f'{WORKDIR}/config.cfg'
cp.read(CONFIG_PATH)


SPEC_DATA_ROOT = cp.get('GENERATOR','spec')

def analyze_API_name(spec_file):
    # informative subwords collected from paper: Understanding and Detecting Disordered Error Handling with Precise Function Pairing
    subwords1 = ["alloc", "new", "request", "create", "init", "lock", "down", "get", "inc", "register", "charge", "on", "enable", "set", "apply", "pin", "assert", "join", "add", "map", "reserve", "begin", "start", "open", "setup"]
    # informative subwords collected by our API name analysis. 
    subwords2 = ['get','find', 'alloc', 'lookup','request','new']
    subwords_all = subwords1+subwords2
    analyze_the_util_API_name(subwords_all,spec_file)


def analyze_API_usage(spec_file):
    calculate_usage_stats(spec_file)


def analyze_API_Doc(spec_file):
    doc_file = f'{WORKDIR}/APIAritifactEval/DocData/kernel_api_doc'
    API_doc_analysis(spec_file, doc_file)


def pipeline(spec_file):
    analyze_API_name(spec_file)
    analyze_API_usage(spec_file)
    analyze_API_Doc(spec_file)


if __name__ == "__main__":
    spec_file = 'SpecGeneration/Data/ReferenceData/All_generated_paired_specs.json'
    spec_file = os.path.join(WORKDIR,  spec_file)
    pipeline(spec_file)
