# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# checkurl.py
# Check URLs in geojson of tiled datasets to confirm they resolve.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-03-11
# Modified: 
#------------------------------------------------------------------------------


import requests
import logging
import datetime
import os
import json
import argparse


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("searchPath", help="Path to geojson or geojsons.")

    # Optional arguments
    parser.add_argument("-v", "--verbose", help="Write successful responses to log as well.", dest='verbose', action='store_true')

    # Print version
    parser.add_argument("--version", action="version", version="%(prog)s - Version 1.0")

    # Parse arguments
    args = parser.parse_args()

    return args

def check_urls(search_path, verbose):
    # Parameters
    # search_path = "test datasets/adams-2010-BareEarthPointsLAS.geojson"

    # Start log
    logging.basicConfig(filename='urlcheck.log', encoding='utf-8', level=logging.INFO, filemode='w')
    start = datetime.datetime.now()
    logging.info("Started: {}".format(start.strftime('%Y-%m-%d %H:%M:%S')))

    # Datasets to check
    datasets = []

    # If search path is single file
    if os.path.isfile and os.path.splitext(search_path)[1] == ".geojson":
        datasets.append(search_path)

    # If search path is directory
    else: 
        for filename in os.listdir(search_path):
        
            # Get file name and extension
            f = os.path.join(search_path, filename)
            extension = os.path.splitext(filename)[1]

            # If geojson, add dataset to list
            if extension == ".geojson":
                datasets.append(f)

    # For each dataset
    for dataset in datasets:

        # Load dataset
        with open(dataset, 'r') as f:
            data = json.load(f)

        # Generate list of urls to check
        urls = []
        for feature in data['features']:
            urls.append(feature['properties']['downloadUrl'])

        # Check each url
        for url in urls:

            # HEAD request (faster than GET request as we are ignoring the body)
            response = requests.head(url)

            # If good skip
            if response.status_code == 200: 
                if verbose: logging.info("{} 200".format(url))
                else: pass

            # If not good, add warning to log
            else: logging.warning("{} does not exist".format(url))

    # End log
    end = datetime.datetime.now()
    logging.info("Ended: {}".format(end.strftime('%Y-%m-%d %H:%M:%S')))
    elapsed_time = end - start
    m, s = divmod(elapsed_time.total_seconds(), 60)
    h, m = divmod(m, 60)
    logging.info("Time to complete: {} hours, {} minutes, {} seconds".format(h, m, s))

if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Run function
    check_urls(args.searchPath, args.verbose)