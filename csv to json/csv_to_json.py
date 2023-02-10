# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# csv_to_json.py
# Convert geodata csv to json.
# Mallory Johnson (mjohnson58@wisc.edu)
# Created: 2023-02-03
# Modified: 2023-02-10
#------------------------------------------------------------------------------

import csv
import json
import os


# Define variables
wd = os.path.dirname(__file__)
input_name = "WGNHS_GeoData.csv"
input_file = os.path.join(wd, input_name)
output_dir = os.path.join(wd, "output/")

schema = ['dc_identifier', 'layer_slug', 'dc_title', 'dc_description', 'dct_provenance_s', 'dct_isPartOf', 'dc_creator_s', 'dc_type', 'dc_subject', 'layer_geom_type', 'dc_format', 'dc_language', 'dct_temporal', 'solr_year', 'download_URL', 'information_URL', 'Envelope', 'uw_supplemental', 'Geographic_Extent', 'Notes']
# Keys from GBL template
# ["geoblacklight_version", "dc_identifier_s", "dc_title_s", "dc_description_s", "dc_rights_s", "dct_provenance_s", "layer_id_s", "layer_slug_s", "layer_geom_type_s", "layer_modified_dt", "dc_format_s", "dc_language_s", "dct_isPartOf_sm", "dc_creator_sm", "dc_publisher_sm", "dc_type_s", "dc_subject_sm", "dct_spatial_sm", "dct_temporal_sm", "solr_year_i", "dct_issued_s", "dct_references_s", "solr_geom", "thumbnail_path_ss", "uw_supplemental_s", "uw_notice_s", "uw_deprioritize_item_b" ]
gbl_template = {
    "geoblacklight_version": "1.0",
    "dc_identifier_s": "REQUIRED: Unique ID",
    "dc_title_s": "REQUIRED",
    "dc_description_s": "REQUIRED: Dataset Description",
    "dc_rights_s": "Public",
    "dct_provenance_s": "Wisconsin Geological and Natural History Survey",
    "layer_id_s": "",
    "layer_slug_s": "REQUIRED: Unique ID",
    "layer_geom_type_s": "Mixed",
    "layer_modified_dt": "2023-01-02T00:00:00Z",
    "dc_format_s": "Multiple Formats",
    "dc_language_s": "English",
    "dct_isPartOf_sm": ["Geology and Groundwater"],
    "dc_creator_sm": ["Wisconsin Geological and Natural History Survey"],
    "dc_publisher_sm": "",
    "dc_type_s": "Dataset",
    "dc_subject_sm": [
        "REQUIRED: ISO category",
        "OPTIONAL: Additional ISO category" ],
    "dct_spatial_sm": [
        ""],
    "dct_temporal_sm": [
        "REQUIRED: Insert year or range here"  ],
    "solr_year_i": 9999,
    "dct_issued_s": "",
    "dct_references_s": "{\"http://schema.org/downloadUrl\":\"https://gisdata.wisc.edu/public/FILENAME.zip\",\"http://www.isotc211.org/schemas/2005/gmd/\":\"https://gisdata.wisc.edu/public/metadata/INSERT UUID HERE - do not remove trailing backslash\"}",
    "solr_geom": "ENVELOPE(West,East,North, South)",
    "thumbnail_path_ss": "",
    "uw_supplemental_s": "",
    "uw_notice_s": "",
    "uw_deprioritize_item_b": False
}


# Reads csv file from file to a dictionary 
def read_csv(file_path):
    rows = []
    # Open csv file
    with open(input_file, 'r') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows

# Check header of input csv to see if it matches schema, raises exception if expected key(s) are missing
def check_header(schema, header):
    if not all(item in header for item in schema):
        raise Exception("Header doesn't match schema; missing 1 or more column headers.")
    return 
    

def create_json(schema, gbl_template, row, output_dir):
    # Create list of keys to be present in output JSON, order matters!
    key_list = schema + [key for key in list(row) if key not in schema]

    # Create empty dictionary to store output data
    out_json = {}
    
    # Iterate through key_list to collect values for output JSON
    for key in key_list:
        
        # If a value in row is not null
        if row[key]:
            out_json[key] = row[key]

        # Else if value is not in row, see if it is in template
        elif key in list(gbl_template):
            out_json[key] = gbl_template[key]

        # Otherwise, value is empty string
        else:
            out_json[key] = ""
        
    # Create output path and write to file
    output_file = os.path.join(output_dir, row['dc_identifier'] + '.json')
    with open(output_file, 'w') as f:
        json.dump(out_json, f, indent=2)


# Check if output directory exists, if not, create it
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# Read in data from csv
data = read_csv(input_file)

# Checks header for required keys
check_header(schema, data[0])

# Creates JSON and adds it to the output folder
create_json(schema, gbl_template, data[0], output_dir)