# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# coordinate_precision.py
# Read indexed dataset GeoJSON and reduce coordinate precision.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-03-22
# Modified: 
#------------------------------------------------------------------------------


import os
import json
import logging, datetime
import argparse


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Mandatory argument
    parser.add_argument("inPath", help="Path to geojson or geojsons.")
    parser.add_argument("outPath", help="Output path to place updated geojsons.")

    # Optional arguments
    parser.add_argument("-p", "--precision", help="How many digits after the decimial (default=4)", dest='precision', type=int, default=4)
    parser.add_argument("-i", "--indent", help="Indent level. Use None for most compact version. (default=2)", dest='indentation', default=2)
    parser.add_argument("-v", "--verbose", help="Write successful precision changes to log as well.", dest='verbose', action='store_true')

    # Print version
    parser.add_argument("--version", action="version", version="%(prog)s - Version 1.0")

    # Parse arguments
    args = parser.parse_args()

    return args

def coordinate_precicison(in_path, out_path, precision, indentation, verbose):

    # Start log
    logging.basicConfig(filename='coordinate_precision.log', level=logging.INFO, filemode='w')
    start = datetime.datetime.now()
    logging.info("Started: {}".format(start.strftime('%Y-%m-%d %H:%M:%S')))

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

    # Make sure output path exists
    if not os.path.exists(out_path):
        # If it does not yet exist, make it
        os.mkdir(out_path)
        logging.info("Making {}.".format(out_path))


    for dataset in datasets:

        # Open geojson
        with open(dataset, 'r') as f:
            data = json.load(f)

        # Lower precision of tile coordinates
        for feature in data['features']:
            if feature['geometry']['type'] == 'Polygon':
                feature['geometry']['coordinates'][0] = [[round(coord, precision) for coord in coords] for coords in feature['geometry']['coordinates'][0]]

            elif feature['geometry']['type'] == 'MultiPolygon':
                feature['geometry']['coordinates'][0][0] = [[round(coord, precision) for coord in coords] for coords in feature['geometry']['coordinates'][0][0]]
            
            else:
                logging.warning("{} feature {}: Feature type {} is not supported. Skipping!".format(os.path.basename(dataset), data['features'].index(feature), feature['geometry']['type']))

        if verbose:
            logging.info("Updated precision of {} to {}.".format(os.path.basename(dataset), precision))

        with open(os.path.join(out_path, os.path.basename(dataset)), 'w') as f:
            json.dump(data, f, indent=indentation)
    
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

    # Type cast indentation as needed
    if args.indentation=='None': args.indentation=None
    elif args.indentation.isdigit(): args.indentation=int(args.indentation)
    else: raise TypeError('-i/--indent: invalid; must be int or None')

    # Run function
    coordinate_precicison(args.inPath, args.outPath, args.precision, args.indentation, args.verbose)