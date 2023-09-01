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
input_name = "example_input.csv"
input_file = os.path.join(wd, input_name)
output_dir = os.path.join(wd, "output/")


#existing defaults
schema = ["geoblacklight_version", "dc_identifier_s", "dc_title_s", "dc_description_s", "dc_rights_s", "dct_provenance_s", "layer_id_s", "layer_slug_s", "layer_geom_type_s", "layer_modified_dt", "dc_format_s", "dc_language_s", "dct_isPartOf_sm", "dc_creator_sm", "dc_publisher_sm", "dc_type_s", "dc_subject_sm", "dct_spatial_sm", "dct_temporal_sm", "solr_year_i", "dct_issued_s", "download1_url", "download1_label", "download2_url", "download2_label", "IndexMapURL", "infoUrl", "metadataurl", "solr_geom_W", "solr_geom_E", "solr_geom_N", "solr_geom_S", "thumbnail_path_ss", "uw_supplemental_s", "uw_notice_s", "uw_deprioritize_item_b"]

# Keys from GBL template, remove blue keys + yellow keys
# null_lookup = {
#     "dc_identifier_s": "REQUIRED: Unique ID",
#     "dc_title_s": "REQUIRED",
#     "dc_description_s": "REQUIRED: Dataset Description",
#    
#     "dct_provenance_s": "Wisconsin Geological and Natural History Survey",
#     "layer_id_s": "",
#     "layer_slug_s": "REQUIRED: Unique ID",
#     "layer_geom_type_s": "Mixed",
#     "layer_modified_dt": "2023-01-02T00:00:00Z",
#     "dc_format_s": "Multiple Formats",
#     "dc_language_s": "English",
#     "dct_isPartOf_sm": ["Geology and Groundwater"],
#     "dc_creator_sm": ["Wisconsin Geological and Natural History Survey"],
#     "dc_publisher_sm": "",
#     "dc_type_s": "Dataset",
#     "dc_subject_sm": [
#         "REQUIRED: ISO category",
#         "OPTIONAL: Additional ISO category" ],
#     "dct_spatial_sm": [
#         ""],
#     "dct_temporal_sm": [
#         "REQUIRED: Insert year or range here"  ],
#     "solr_year_i": 9999,
#     "dct_issued_s": "",
#     "dct_references_s": "{\"http://schema.org/downloadUrl\":\"https://gisdata.wisc.edu/public/FILENAME.zip\",\"http://www.isotc211.org/schemas/2005/gmd/\":\"https://gisdata.wisc.edu/public/metadata/INSERT UUID HERE - do not remove trailing backslash\"}",
#     "solr_geom": "ENVELOPE(West,East,North, South)",
#     "thumbnail_path_ss": "",
#     "uw_supplemental_s": "",
#     "uw_notice_s": "",
#     "uw_deprioritize_item_b": False
# }

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
    # if not all(item in header for item in schema):
       
    for item in schema:
        if item in header:
            pass
          
        else:
            print(item)
            raise Exception("Header doesn't match schema; missing 1 or more column headers.")

        
    # check for keys with or without multiples

    # check for keys with multiples, key in remaining headers 
    return 
    


def create_json(schema, row, output_dir):
    # Create list of keys to be present in output JSON, order matters!
    header_list = schema + [key for key in list(row) if key not in schema]

    # Create empty dictionary to store output data, all blue + orange
    out_json = { 
        "geoblacklight_version": "1.0",
        "dc_rights_s": "Public",
        "layer_id_s": "",
        "dc_language_s": "English",
        "dc_publisher_sm": "",
        "dct_spatial_sm": [""],
        "dct_issued_s": "",
        "thumbnail_path_ss": "",
        "uw_supplemental_s": "",
        "uw_notice_s": "",
        "uw_deprioritize_item_b": False
    }
    
    solr_geom_values = []

    dct_reference_s_values = []

    # Iterate through key_list to collect values for output JSON
    for key in header_list:
        
        #pseudocode on paper first
        if 'solr_geom' in key:
            # if key contains 'solr_geom':
            #   solr_geom = ENVELOPE({w}, {e}, {n}, {s}).format(solr_geom_w, solr_geom_e, solr_geom_n, solr_geom_s)
            pass

        elif key == 'dct_reference_s':
            # if item in key = 'indexurl'
            #   dct_reference_s = 'indexurl'
            #   ignore downloadurl, metadataurl, infourl
            #elif item in header
            #   dct_references
            pass

        else:

            # If a value in row is not null, included in initial out_json -> value will be overwritten
            if row[key]:
                out_json[key] = row[key]

            # Else value is not in row, see if it is in template
            else:
                #yellow and blue keys in list
                if key in ["geoblacklight_version", "dc_identifier_s", "dc_title_s", "dc_description_s", "dc_rights_s", "dct_provenance_s", "layer_id_s", "layer_slug_s", "layer_geom_type_s", "layer_modified_dt", "dc_format_s", "dc_language_s", "dct_isPartOf_sm", "dc_creator_sm", "dc_publisher_sm", "dc_type_s", "dc_subject_sm", "dct_spatial_sm", "dct_temporal_sm", "solr_year_i", "dct_issued_s", "dct_references_s", "solr_geom"]:
                    #throw error, write in error logic/handling
                    pass

    # Create output path and write to file
    output_file = os.path.join(output_dir, row['dc_identifier_s'] + '.json')
    with open(output_file, 'w') as f:
        json.dump(out_json, f, indent=2)




# Read in data from csv
data = read_csv(input_file)

# Checks header for required keys
check_header(schema, data[0])

# Check if output directory exists, if not, create it
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Iterates through all rows of data
for row in data:
    
    # Creates JSON and adds it to the output folder
    create_json(schema, row, output_dir)