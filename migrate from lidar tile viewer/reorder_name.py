# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# reorder_name.py
# Reorder pieces of filenames in GeoJSONs
# Kuang-Cheng Cheng (kcheng38@wisc.edu)
# Created: 2022-05-24
# Modified: 
#------------------------------------------------------------------------------

# Import libraries
import json
from os.path import basename, dirname, join, splitext



# Parameters
wd = dirname(__file__)
print(wd)
datasets = ["monroe-2010-BareEarthLAS.geojson","monroe-2010-BearEarthSHP.geojson","monroe-2010-CountoursSHP.geojson"]

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

        # Get the filename
        fname, ext = splitext(basename(download_url))

        # Break the filename into pieces (township/range/section)
        # Example: 2 T20 S36 R1 --> 2200136
        [dir, twp, sec, rng] = fname.split(' ')

        new_fname = "{}{:02d}{:02d}{:02d}{}".format(dir, int(twp[1:]), int(rng[1:]), int(sec[1:]), ext)
        
        # Update downloadUrl
        feature["properties"]["downloadUrl"] = "{}/{}".format('/'.join(download_url.split('/')[:-1]), new_fname)

    # Write the GeoJSON to a new file (indent=2)
    with open(out_path, 'w') as f:
        json.dump(metadata, f, indent=2)

