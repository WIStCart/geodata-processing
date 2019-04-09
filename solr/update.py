"""
Update.py

Author(s): Jim Lacy, Ben Segal

Description: 
This script is designed to interact with a Solr instance running the GeoBlacklight 1.0 Schema.  It can perform one of four operations: 
1. Upload and and then ingest a directory of GBL-formatted json files. Optional: recurse into subfolders.
2. Delete a named "collection" from the Solr index
3. Delete a single record from the Index using the unique ID (uuid)
4. Purge the entire Solr index.  The nuclear option!

When processing json inputs, the script performs some basic QA steps before the ingest is run.

All updates to Solr are "auto-committed" (changes are effective immediately)

Dependencies: Python 3.x, pysolr
"""

import os
import json
import argparse
import sys
from collections import OrderedDict
from glob import glob
import fnmatch

# non-standard Python libraries that require additional installation
# e.g., pip install pysolr
import pysolr

"""
 
 to do (Ben?):
 
 add comments throughout code
 connect to solr instance that use https
 connect to solr instance with username and password
 ++ better error catching throughout
 script does not work on json files with multiple records embedded
    Modify this script, or modify other scripts that output combined json???
 Can't have a closing \ at end of input file path 
 pre-scan items in dictionary, look for errors before ingest
 add message to indicate which instance is being worked on (delete, add, purge)
 
"""
 
SOLR_USERNAME = "username"
SOLR_PASSWORD = "password" 
SOLR_URL_DEV = "http://localhost:8983/solr/geodata-core-development/"
SOLR_URL_TEST = "http://geodata-test.sco.wisc.edu/solr/geodata-development/"
SOLR_URL_PRODUCTION = "http://geodata-prod.sco.wisc.edu/solr/geodata-development/"

class SolrInterface(object):

    def __init__(self, url=None):
        # init object and call Solr connection
        self.solr_url = url
        self.solr = self._connect_to_solr()

    def _connect_to_solr(self):
        # establish the connection to Solr instance
        return pysolr.Solr(self.solr_url, always_commit=True)

    def escape_query(self, raw_query):
        # Uncertain if this is really necessary
        return raw_query.replace("'", "\'")

    def delete_query(self, query, no_confirm=False):
        # execute delete query
        s = self.solr.search(self.escape_query(query), **{"rows": "0"})
        if s.hits == 0:
            print("No records found in [instance] instance. Nothing to delete.  Exiting...")
        else:
            are_you_sure = input(
            "Are you sure you want to delete {num_recs} records from [instance] instance? Y/N: ".format(num_recs=s.hits)
            )
            if are_you_sure.lower() == "y":
                self.solr.delete(q=self.escape_query(query))
                print("Done deleting {num_recs} records from [instance] instance...".format(num_recs=s.hits))
            else:
                print("Okay, nothing deleted from [instance] instance. Exiting...")

    def json_to_dict(self, json_doc):
        # read data from one json file
        j = json.load(open(json_doc, "rt", encoding="utf8"))
        print("Reading input file " + json_doc)
        return j


    def add_dict_list_to_solr(self, list_of_dicts):
        # ingest dictionary to Solr
        try:
            self.solr.add(list_of_dicts)
            return True
        except pysolr.SolrError as e:
            print("\n\n*********************")
            print("Solr Error: {e}".format(e=e))
            print("*********************\n\n")
            return False

    
class Update(object):

    def __init__(self, SOLR_USERNAME, SOLR_PASSWORD, COLLECTION, UUID, INSTANCE, TO_JSON=False, RECURSIVE=False, PURGE=False):
        self.RECURSIVE = RECURSIVE
        self.PURGE = PURGE
        if INSTANCE=="prod":
            SOLR_URL = SOLR_URL_PRODUCTION
        elif INSTANCE=="test":
            SOLR_URL = SOLR_URL_TEST
        elif INSTANCE=="dev":
            SOLR_URL = SOLR_URL_DEV
        else: 
            # if instance not specified, default to dev
            SOLR_URL = SOLR_URL_DEV

        # the following formating does not work.  needs attention.
        #if SOLR_USERNAME and SOLR_PASSWORD:
            #SOLR_URL = SOLR_URL.format(username=SOLR_USERNAME, password=SOLR_PASSWORD)    

        #print("Solr URL: " + SOLR_URL)
        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
           
    def scan_dict_records(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        print("Performing QA scan...")
        status = True  # always set to true for now
        """ 
        stuff to test:
            1. Do all required elements have data? (dc_identifier_s, layer_slug_s, dc_title_s,solr_geom, dct_provenance_s, dc_rights_s, geoblacklight_version)
            2. Bad characters or encodings?
            3. "NaN" in solr_geom?
            3. More stuff as we get additional experience
        """
        # 1. scan required elements
        #
        # read through each item in list
        # check the required elements to make sure they are not empty
        # check to make sure no elements contain "Nan" (null???).  
        # if any element fails, output message and dc_title_s and layer_slug_s, return false
        # otherwise return true
        
        return status
        
    def get_files_from_path(self, start_path, criteria="*"):
        # construct a list of json files to read
        # process fails if input directory contains a trailing \
        files = []
        if self.RECURSIVE:
            for path, folder, ffiles in os.walk(start_path):
                for i in fnmatch.filter(ffiles, criteria):
                    files.append(os.path.join(path, i))
        else:
            files = glob(os.path.join(start_path, criteria))
        return files

    def add_json(self, path_to_json):
        # cycle through json files, add them to a dictionary object
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        #print(files)
        if files: 
            dicts = []
            for i in files:
                dicts.append(self.solr.json_to_dict(i))       
            if self.scan_dict_records(dicts):
                print("QA health check passed.")
                ingest_result = self.solr.add_dict_list_to_solr(dicts)
                print("Ingest result: " + str(ingest_result))
                if ingest_result:
                    print("Added {n} records to Solr [instance] instance.".format(n=len(dicts)))
                else:   
                    print("Solr ingest on [instance] failed.  Exiting...")
            else:
                print("QA health check failed.  Exiting...") 
        else:
            print("No files found.  Exiting...")
        
    
    def delete(self, uuid):
        # setup query to delete a single record
        # the delete operation is handled by delete_query
        self.solr.delete_query("layer_slug_s:" + self.uuid)
        
    def delete_collection(self, collection):
        # setup query to delete an entire collection
        print("Collection passed is: " + self.collection)
        self.solr.delete_query("dct_isPartOf_sm:" + '"' + self.collection + '"')
        
    def purge(self):
        # setup query to purge all records from Solr
        self.solr.delete_query("*:*")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--recursive",
        action='store_true',
        help="Recurse into subfolders when adding JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-aj",
        "--add-json",
        help="Indicate path to folder with GeoBlacklight \
              JSON files that will be uploaded.") 
    group.add_argument(
        "-dc",
        "--delete-collection",
        help="Remove an entire collection from the Solr index.")               
    group.add_argument(
        "-d",
        "--delete",
        help="Delete the provided unique record ID (layer_slug) \
            from the Solr index.")  
    group.add_argument(
        "-p",
        "--purge",
        action='store_true',
        help="Delete the entire Solr index.") 
    group = parser.add_mutually_exclusive_group(required=False)   
    group.add_argument(
        "-i",
        "--instance",
        choices={"prod", "test","dev"},
        help="Identify which instance of Solr to use.")           
    
    args = parser.parse_args()
    interface = Update(SOLR_USERNAME, SOLR_PASSWORD, COLLECTION=args.delete_collection, UUID=args.delete,INSTANCE=args.instance, RECURSIVE=args.recursive, PURGE=args.purge)
    #print(args)

    if args.add_json:
        interface.add_json(args.add_json)
    elif args.delete_collection:
        interface.delete_collection(args.delete_collection)        
    elif args.delete:
        interface.delete(args.delete)
    elif args.purge:
        interface.purge()
    else:
        sys.exit(parser.print_help())

if __name__ == "__main__":
    sys.exit(main())
