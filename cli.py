import argparse

ACTIONS = [
    "scan",
    "upload"
]

VERSION = "0.0.1"

def create_parser():
    parser = argparse.ArgumentParser(prog="arduboy_toolset", description='Tools for working with Arduboy')
    parser.add_argument("action", choices=ACTIONS, help="Tool/action to perform")
    parser.add_argument("-i", "--input_file", help="Input file for given command", default="infile")
    parser.add_argument("-o", "--output_file", help="Output file for given command", default="outfile")
    parser.add_argument("-m", "--multi", action="store_true", help="Enable multi-device-mode (where applicable)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser