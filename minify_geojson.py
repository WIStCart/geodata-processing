# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# minify_geojson.py
# Minifiy geojson.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-04-21
# Modified: 
#------------------------------------------------------------------------------


import argparse
from indextools import minify_geojson


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("path", help="Path to geojson or geojsons.")

    # Optional arguments
    parser.add_argument("-i", "--indent", help="Indent level. (default=None)", dest='indentation', type=int, default=None)

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    minify_geojson(args.path, args.indentation)