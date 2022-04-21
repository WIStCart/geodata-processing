# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# update_url.py
# Update websiteUrl of geojson to specified new url.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-04-21
# Modified: 
#------------------------------------------------------------------------------


import argparse
from indextools import update_url


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("path", help="Path to geojson or geojsons.")
    parser.add_argument("newUrl", help="The new websiteUrl.")

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    update_url(args.path, args.newUrl)