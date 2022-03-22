# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# migrate.py
# Migrate tile indecies for lidar data from the lidar tile viewer to geodata@wi
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-02-08
# Modified: 2022-03-22
#------------------------------------------------------------------------------


import json
from operator import indexOf
from os.path import join, dirname
import copy
import logging
import datetime
import re


# Parameters
deliveries = ['adams', 'ashland', 'bayfield', 'buffalo', 'burnett', 'calumet', 'clark', 'columbia', 'crawford', 'dane', 'madison', 'dodge', 'douglas', 'cityOfSuperior', 'eauClaire', 'cityOfEauClaire', 'florence', 'fondDuLac', 'forest', 'grant', 'green', 'iowa', 'iron', 'jefferson', 'juneau', 'kewaunee', 'lacrosse', 'lafayette', 'langlade', 'lincoln', 'manitowoc', 'marinette', 'marquette', 'monroe19', 'oneida', 'ozaukee', 'pepin', 'pierce', 'polk', 'portage', 'price', 'racine', 'racine17', 'richland', 'rusk', 'sauk', 'sawyer', 'shawano', 'stcroix', 'taylor', 'trempealeau', 'vernon', 'washburn', 'washington', 'waushara', 'winnebago', 'wood', 'adams3DEP', 'calumet3DEP', 'fondDuLac3DEP', 'greenLake3DEP', 'jefferson3DEP', 'lafayette3DEP', 'oconto', 'pepin3DEP', 'sheboygan', 'waupaca3DEP']
wd = dirname(__file__)
layers_dir = join(dirname(dirname(wd)), "lidar-data-inventory/tile-search/layers/")
metadata_file = join(dirname(dirname(wd)), "lidar-data-inventory/tile-search/assets/metadata.js")


# Start log
logging.basicConfig(filename='migrate.log', encoding='utf-8', level=logging.DEBUG, filemode='w')
start = datetime.datetime.now()
logging.info("Started: {}".format(start.strftime('%Y-%m-%d %H:%M:%S')))


# Load metadata
with open(metadata_file, 'r') as f:
    raw = re.sub(r'([^ ]*[^:])(?=: {)', r'"\1"', f.read().lstrip("var metadata = ").replace("};", "}"))
    metadata = json.loads(raw)

# For each delivery
for delivery in deliveries:
    in_file = "{}.geojson".format(delivery)

    # Construct full input file path
    in_path = join(layers_dir, in_file)

    # Open geojson
    with open(in_path, 'r') as f:
        data = json.load(f)

    # Lower precision of tile coordinates
    for feature in data['features']:
        if feature['geometry']['type'] == 'Polygon':
            feature['geometry']['coordinates'][0] = [[round(coord, 4) for coord in coords] for coords in feature['geometry']['coordinates'][0]]

        if feature['geometry']['type'] == 'MultiPolygon':
            feature['geometry']['coordinates'][0][0] = [[round(coord, 4) for coord in coords] for coords in feature['geometry']['coordinates'][0][0]]


    # For each dataset in delivery
    for dataset in metadata[delivery]['datasets']:

        # Create copy of data to edit
        temp_data = copy.deepcopy(data)
        
        # Construct full output file path
        out_file = "output/{}-{}-{}.geojson".format(delivery, metadata[delivery]['year'], dataset['name'].replace(" ", ""))
        out_path = join(wd, out_file)

        # Skip if not tiled
        tiled = dataset['tiled']
        if not tiled: continue

        # Fetch metadata for dataset
        name = dataset['name']
        base_url = dataset['baseURL']
        url_exts = dataset['URLexts']

        # Skip and warn if more than one extension
        if len(url_exts) > 1 and not url_exts[0] in ['.las','.LAS']:
            logging.warning("More than one extension for {} {}: {}; skipping!".format(delivery, metadata[delivery]['year'], dataset['name']))
            continue
        elif url_exts[0] in ['.las','.LAS'] and len(url_exts)>1:
            logging.info("las and lasx for {} {}: {}; skipping other extensions.".format(delivery, metadata[delivery]['year'], dataset['name']))

        # For each tile
        for feature in temp_data['features']:
            tile_name = str(feature['properties']['tileName'])

            # Build properties
            title = tile_name
            label = tile_name
            download_url = base_url + tile_name + url_exts[0]
            website_url = base_url[:base_url.rindex('/')]

            # Redefine properties
            feature['properties'] = {
                'title': title,
                'label': label,
                'downloadUrl': download_url,
                'websiteUrl': website_url,
            }


        # Write dataset geojson to file from temp_data
        with open(out_path, 'w') as f:
            json.dump(temp_data, f, indent=2)


# End log
end = datetime.datetime.now()
logging.info("Ended: {}".format(end.strftime('%Y-%m-%d %H:%M:%S')))
elapsed_time = end - start
m, s = divmod(elapsed_time.total_seconds(), 60)
h, m = divmod(m, 60)
logging.info("Time to complete: {} hours, {} minutes, {} seconds".format(h, m, s))