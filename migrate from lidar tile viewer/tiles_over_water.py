# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# tiles_over_water.py
# Remove tile from index geojson if all datasets for delivery are missing the
#     tile.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-06-17
# Modified: 
#------------------------------------------------------------------------------

# Import libraries
import json
from os.path import dirname, join
import requests
from copy import deepcopy



# Parameters
wd = dirname(__file__)
tile_search_dir = join(wd, "../../lidar-data-inventory/tile-search/layers/")
index_dir = join(wd, "output/")
output_dir = join(wd, "fixed/")



# Config consisting of tile viewer geojson and each dataset's index geojson
datasets = [
    {
        'tiles': "marinette.geojson",
        'indices': [
            "marinette-2014-PointsCalibratedRawSwath.geojson",
            "marinette-2014-PointsClassifiedLAS.geojson"
        ]
    },
    {
        'tiles': "ashland.geojson",
        'indices': ["ashland-2014-ClassifiedPoints.geojson"]
    }
]

# For each dataset
for dataset in datasets:

    # Build paths
    tiles_geojson = join(tile_search_dir, dataset['tiles'])
    indices = [index for index in dataset['indices']]

    # Get set of tiles from tile viewer geojson (lidar-data-inventory/tile-search/layers/)
    with open(tiles_geojson, "r") as f:
        tiles_data = json.load(f)

    tiles = set(feature['properties']['tileName'] for feature in tiles_data['features'])

    print(dataset['tiles'])
    print(len(tiles))

    # Iterate through each index
    for index in indices:

        # Open index
        with open(join(index_dir, index), "r") as f:
            index_data = json.load(f)

        # Iterate through each feature of index
        for feature in index_data['features']:

            # Check downloadUrl of each feature; HEAD request (faster than GET request as we are ignoring the body)
            response = requests.head(feature['properties']['downloadUrl'])

            # If 200, discard tile from set (we use set and discard instead of list and remove since trying to remove a value that does not exist in list gives a ValueError)
            if response.status_code == 200:
                tiles.discard(feature['properties']['title'])

        print(len(tiles))

    # Remaining list of tiles are missing from all datasets so should be removed 
    # Iterate through each index
    for index in indices:

        # Open index
        with open(join(index_dir, index), "r") as f:
            index_data = json.load(f)

        # Create a copy of the data to edit
        temp_data = deepcopy(index_data)


        # Iterate through each feature of index
        for feature in index_data['features']:

            # If feature in tile list, remove feature from geojson
            if feature['properties']['title'] in tiles:
                temp_data['features'].remove(feature)

        # Save updated index geojson to file
        with open(join(output_dir, index), 'w') as f:
            json.dump(temp_data, f, indent=2)