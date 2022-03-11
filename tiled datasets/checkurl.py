# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# checkurl.py
# Check URLs in geojson of tiled datasets to confirm they resolve.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-03-11
# Modified: 
#------------------------------------------------------------------------------


from pyexpat import features
import requests
import logging
import datetime
import os
import json


# Parameters
search_path = "test datasets/"

# Start log
logging.basicConfig(filename='urlcheck.log', encoding='utf-8', level=logging.INFO, filemode='w')
start = datetime.datetime.now()
logging.info("Started: {}".format(start.strftime('%Y-%m-%d %H:%M:%S')))

# Datasets to check
datasets = []
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
        if response.status_code == 200: pass

        # If not good, add warning to log
        else: logging.warning("{} does not exist".format(url))

# End log
end = datetime.datetime.now()
logging.info("Ended: {}".format(end.strftime('%Y-%m-%d %H:%M:%S')))
elapsed_time = end - start
m, s = divmod(elapsed_time.total_seconds(), 60)
h, m = divmod(m, 60)
logging.info("Time to complete: {} hours, {} minutes, {} seconds".format(h, m, s))