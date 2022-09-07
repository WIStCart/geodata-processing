# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# regex_name.py
# Use regex to fix filenames of lidar tile index geojsons
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-06-03
# Modified: 
#------------------------------------------------------------------------------

# Import libraries
import json
from os.path import dirname, join
import re



# Parameters
wd = dirname(__file__)
print(wd)
datasets = ["marquette-2018-PointsClassifiedLAS.geojson"]

# Iterate through datasets
for dataset in datasets:

    # Build paths
    file_path = join(wd, "output/", dataset)
    out_path = join(wd, "fixed/", dataset)
    print(file_path)

    # Open geojson 
    with open(file_path, "r") as f:
        metadata = json.load(f)

    # Iterrate through features
    for feature in metadata['features']:
        # Read the download URL
        download_url = feature["properties"]["downloadUrl"]

        # Update download URL using regular expresion
        feature["properties"]["downloadUrl"] = re.sub("(?<=USGS_LPC_WI_FEMAHQ_2018_16T)C(?=P2)", "B", download_url)

    # Write the GeoJSON to a new file (indent=2)
    with open(out_path, 'w') as f:
        json.dump(metadata, f, indent=2)