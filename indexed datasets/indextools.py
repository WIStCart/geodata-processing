# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# indextools.py
# Tools for indexed datasets used in geodata@wisc
# Hayden Elza (elza@wisc.edu)
# Jim Lacy (lacy@wisc.edu)
# Created: 2022-04-21
# Modified: 2024-06-21
#------------------------------------------------------------------------------


import os
import logging, datetime
import json
import requests
from requests.exceptions import *
from urllib.parse import urlparse
      
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

def coordinate_precision(in_path, out_path, precision, indentation, skip_feature, verbose):

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
        
        # Create a session for this check.  This seems to avoid creating security/DDOS concerns 
        # by re-using the same connection.
        session = requests.Session()
               
        # Check each url
        print(f"Checking links in {os.path.basename(dataset)}...")
        logging.info(f"Checking links in {os.path.basename(dataset)}...")
        
        for url in urls:           
            try:
                response = session.head(url, timeout=5) 
                if response.status_code == 200:
                    pass
                else: 
                    logging.warning(f"Not Found: {url}")
                    print(f"Not Found: {url}")
            except requests.RequestException as e:
                # exception will be thrown if the server can't be reached
                print(f"Error connecting to server {urlparse(url).netloc}")
                logging.info(f"Error connecting to server {urlparse(url).netloc}")
        
        session.close()
    
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

def update_url(path, new_url):

    # Datasets to process
    datasets = get_datasets_list(path)

    # For each dataset
    for dataset in datasets:

        # Read geojson
        with open(dataset, 'r') as f:
            data = json.load(f)
        
        # For each feature
        for feature in data['features']:

            # Update websiteUrl
            feature['properties']['websiteUrl'] = new_url

    # Write update geojson to file
    with open(dataset, 'w') as f:
            json.dump(data, f)

def remove_missing_tiles(in_path, out_path, indentation, verbose):

    from copy import deepcopy

    # Start log
    log = logger('remove_missing_tiles_{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H%M')))
    log.start()

    # Datasets to process
    datasets = get_datasets_list(in_path)

    # For each dataset
    for dataset in datasets:

        # Open dataset
        with open(dataset, "r") as f:
            data = json.load(f)

        # Create a copy of the data to edit
        temp_data = deepcopy(data)
        
        logging.info(f"Processing {os.path.basename(dataset)}...")
        print(f"Processing {os.path.basename(dataset)}...")
        
        # Create a session for this check.  This seems to avoid creating security/DDOS concerns 
        # by re-using the same connection.
        session = requests.Session()
        
        # Iterate through each feature of data
        for feature in data['features']:                
            url = feature['properties']['downloadUrl']           
            try:
                # Check downloadUrl of each feature; HEAD request (faster than GET request as we are ignoring the body)
                response = session.head(url, timeout=5) 
                       
                # If not good, give warning and remove from geojson
                # This assumes the user has already run a url check, and is ready to pull tiles that give a 404!
                if response.status_code == 404:
                    temp_data['features'].remove(feature)
                    logging.info(f"{url} >>> Tile removed from GeoJSON index.")
                    print(f"{url} >>> Tile removed from GeoJSON index.")
            except requests.RequestException as e:
                # exception will be thrown if the server can't be reached
                print(f"Error connecting to server {urlparse(url).netloc}")
                logging.info(f"Error connecting to server {urlparse(url).netloc}")
         
        session.close()
            
        # Save updated index geojson to file
        with open(os.path.join(out_path, os.path.basename(dataset)), 'w') as f:
            json.dump(temp_data, f, indent=indentation)
    
    # End log
    log.end()