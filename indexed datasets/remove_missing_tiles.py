# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# remove_missing_tiles.py
# Remove tiles from index geojson where downloadUrl returns 404.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-06-21
# Modified: 
#------------------------------------------------------------------------------


import argparse
from indextools import remove_missing_tiles


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("inPath", help="Path to geojson or geojsons.")
    parser.add_argument("outPath", help="Output path to place updated geojsons.")

    # Optional arguments
    parser.add_argument("-i", "--indent", help="Indent level. (default=None)", dest='indentation', type=int, default=None)
    parser.add_argument("-v", "--verbose", help="Write successful precision changes to log as well.", dest='verbose', action='store_true')

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    remove_missing_tiles(args.inPath, args.outPath, args.indentation, args.verbose)