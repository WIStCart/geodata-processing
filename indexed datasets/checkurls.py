# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# checkurls.py
# Check URLs in geojson of tiled datasets to confirm they resolve.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-03-11
# Modified: 2022-04-21
#------------------------------------------------------------------------------


import argparse
from indextools import check_urls


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("searchPath", help="Path to geojson or geojsons.")

    # Optional arguments
    parser.add_argument("-v", "--verbose", help="Write successful responses to log as well.", dest='verbose', action='store_true')

    # Print version
    parser.add_argument("--version", action="version", version="%(prog)s - Version 1.1")

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    check_urls(args.searchPath, args.verbose)