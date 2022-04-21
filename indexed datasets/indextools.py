# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# indextools.py
# Tools for indexed datasets used in geodata@wisc
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-04-21
# Modified: 
#------------------------------------------------------------------------------


import os
import logging, datetime
import json
import requests


class logger:
    
    def __init__(self, filename, level=logging.INFO, filemode='w'):
        self.filename = filename
        self.level = level
        self.filemode = filemode

    def start(self):
        logging.basicConfig(filename=self.filename, level=self.level, filemode=self.filemode)
        self.start = datetime.datetime.now()
        logging.info("Started: {}".format(self.start.strftime('%Y-%m-%d %H:%M:%S')))

    def end(self):
        end = datetime.datetime.now()
        logging.info("Ended: {}".format(end.strftime('%Y-%m-%d %H:%M:%S')))
        elapsed_time = end - self.start
        m, s = divmod(elapsed_time.total_seconds(), 60)
        h, m = divmod(m, 60)
        logging.info("Time to complete: {} hours, {} minutes, {} seconds".format(h, m, s))

def get_datasets_list(in_path):

    # Datasets to check
    datasets = []

    # If input path is single file
    if os.path.isfile and os.path.splitext(in_path)[1] == ".geojson":
        datasets.append(in_path)

    # If input path is directory
    else: 
        for filename in os.listdir(in_path):
        
            # Get file name and extension
            f = os.path.join(in_path, filename)
            extension = os.path.splitext(filename)[1]

            # If geojson, add dataset to list
            if extension == ".geojson":
                datasets.append(f)

    return datasets

def reduce_precision(dataset, out_path, precision, indentation, skip_feature, verbose):

    # Open geojson
    with open(dataset, 'r') as f:
        data = json.load(f)

    # Lower precision of tile coordinates
    for feature in data['features']:

        # Polygon
        if feature['geometry']['type'] == 'Polygon':
            feature['geometry']['coordinates'][0] = [[round(coord, precision) for coord in coords] for coords in feature['geometry']['coordinates'][0]]

        # MultiPolygon
        elif feature['geometry']['type'] == 'MultiPolygon':
            feature['geometry']['coordinates'][0][0] = [[round(coord, precision) for coord in coords] for coords in feature['geometry']['coordinates'][0][0]]

        # Point
        elif feature['geometry']['type'] == 'Point':
            feature['geometry']['coordinates'] = [round(coord, precision) for coord in feature['geometry']['coordinates']]
        
        # Other
        else:

            # If flag to skip only feature is used
            if skip_feature:
                logging.warning("{} feature {}: Feature type {} is not supported. Skipping!".format(os.path.basename(dataset), data['features'].index(feature), feature['geometry']['type']))

            # Else skip entire dataset
            else:
                logging.warning("{} feature {}: Feature type {} is not supported. Skipping Dataset!".format(os.path.basename(dataset), data['features'].index(feature), feature['geometry']['type']))
                return

        # Log dataset if verbose flag used
    if verbose:
        logging.info("Updated precision of {} to {}.".format(os.path.basename(dataset), precision))

    # Write updated json to file
    with open(os.path.join(out_path, os.path.basename(dataset)), 'w') as f:
        json.dump(data, f, indent=indentation)

    return

def coordinate_precicison(in_path, out_path, precision, indentation, skip_feature, verbose):

    # Start log
    log = logger('coordinate_precision.log')
    log.start()

    # Datasets to process
    datasets = get_datasets_list(in_path)

    # Make sure output path exists
    if not os.path.exists(out_path):

        # If it does not yet exist, make it
        os.mkdir(out_path)
        logging.info("Making {}.".format(out_path))


    for dataset in datasets:
        reduce_precision(dataset, out_path, precision, indentation, skip_feature, verbose)
    
    # End log
    log.end()

def check_urls(search_path, verbose):

    # Start log
    log = logger('urlcheck.log')
    log.start()

    # Datasets to check
    datasets = get_datasets_list(search_path)

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
                if verbose: logging.info("{} {} 200".format(os.path.basename(dataset), url))
                else: pass

            # If not good, add warning to log
            else: logging.warning("{} {} {}".format(os.path.basename(dataset), url, response.status_code))

    # End log
    log.end()

def minify_geojson(path, indentation):

    # Datasets to process
    datasets = get_datasets_list(path)

    # For each dataset
    for dataset in datasets:

        # Read geojson
        with open(dataset, 'r') as f:
            data = json.load(f)

        # Write with desired indent
        with open(dataset, 'w') as f:
            json.dump(data, f, indent=indentation)
