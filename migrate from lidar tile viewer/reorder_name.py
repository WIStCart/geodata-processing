# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# reorder_name.py
# Reorder pieces of filenames in GeoJSONs
# Kuang-Cheng Cheng (kcheng38@wisc.edu)
# Created: 2022-05-24
# Modified: 
#------------------------------------------------------------------------------

## filename: 
# monroe-2010-BareEarthLAS.geojson
# monroe-2010-BearEarthSHP.geojson
# monroe-2010-CountoursSHP.geojson

# Import libraries
import json
from os.path import basename

# Open geojson 
file_path = "C:\\Users\\mlstudent\\Documents\\GitHub\\geodata-processing\\migrate from lidar tile viewer\\output\\monroe-2010-BareEarthLAS.geojson"
with open(file_path, "r") as f:
    metadata = json.load(f)

# Iterrate through features
for feature in metadata['features']:
    # Read the download URL
    dwnload_url = feature["properties"]["downloadUrl"]

    # Get the filename
    f_name = basename(dwnload_url)

    # Break the filename into pieces (township/range/section)
    name_0 = f_name[0]
    name_ts = f_name[3:5]
    name_r = f_name[-6:-4]
    name_s = f_name[7:9]
    name_ext = f_name[-4:]
    try:
        name_r = int(name_r)
        name_r = str(name_r)
    except:
        name_r = f_name[-5:-4]
    try:
        name_s = int(name_s)
        name_s = str(name_s)
    except:
        name_s = f_name[8:9]

    # Concatenate a new filename (Use zfill)
    url_dir_leng = len(dwnload_url)-len(f_name)
    url_1stPart = dwnload_url[:url_dir_leng]
    name_r_2d = name_r.zfill(2)
    name_s_2d = name_s.zfill(2)
    new_f_name = name_0 + name_ts + name_r_2d + name_s_2d + name_ext

    # Store new filename into download URL
    new_url = url_1stPart + new_f_name
    feature["properties"]["downloadUrl"] = new_url

# # Check the result
# for i in range(len(metadata['features'])):
#     print(metadata["features"][i]["properties"]["downloadUrl"])

# Write the GeoJSON to a new file (indent=2)
with open("C:\\Users\\mlstudent\\Documents\\GitHub\\geodata-processing\\migrate from lidar tile viewer\\fixed\\monroe-2010-BareEarthLAS.geojson", 'w') as f:
    json.dump(metadata, f, indent=2)

