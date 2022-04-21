# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# coordinate_precision.py
# Read indexed dataset GeoJSON and reduce coordinate precision.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-03-22
# Modified: 2022-04-21
#------------------------------------------------------------------------------


import argparse
from indextools import coordinate_precicison


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("inPath", help="Path to geojson or geojsons.")
    parser.add_argument("outPath", help="Output path to place updated geojsons.")

    # Optional arguments
    parser.add_argument("-p", "--precision", help="How many digits after the decimial (default=4)", dest='precision', type=int, default=4)
    parser.add_argument("-i", "--indent", help="Indent level. (default=None)", dest='indentation', type=int, default=None)
    parser.add_argument("-s", "--skip-feature", help="Gracefully skip feature instead of entire dataset if there is an unsupported geometry type.", dest='skip_feature', action='store_true')
    parser.add_argument("-v", "--verbose", help="Write successful precision changes to log as well.", dest='verbose', action='store_true')

    # Print version
    parser.add_argument("--version", action="version", version="%(prog)s - Version 1.1")

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    coordinate_precicison(args.inPath, args.outPath, args.precision, args.indentation, args.skip_feature, args.verbose)