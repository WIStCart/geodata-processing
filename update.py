"""
Update.py
 
Author(s): Jim Lacy, Ben Segal, Eli Wilz
  
Description: 
This script is designed to interact with a Solr instance running the GeoBlacklight 1.0 Schema.  It can perform one of five operations: 
1. Upload and and then ingest a directory of GBL-formatted json files. Optional: recurse into subfolders.
2. Delete a named "collection" from the Solr index
3. Delete a single record from the Index using the unique ID (uuid)
4. Delete all records from a specified repository (a.k.a. dct_provenance_s, a.k.a. "Held by")
5. Purge the entire Solr index.  The nuclear option!

When processing json inputs, the script performs some basic QA steps before the ingest is run.

All updates to Solr are "auto-committed" (changes are effective immediately)

Dependencies: Python 3.x, pysolr


to-do:
- Change Argument Names to Something more universally understood (Consult with Jim Here)

- Update Syntax to remove duplicate Print Statements 

- Develop UI or GUI  


"""

import os
import time
import json
import argparse
import sys
import shutil
from collections import OrderedDict
from glob import glob
import fnmatch
import requests
from requests.auth import HTTPBasicAuth
from config import *


# non-standard Python libraries that require additional installation
# e.g., pip install pysolr
import pysolr


class SolrInterface(object):

    def __init__(self, url=None):
        # init object and call Solr connection
        self.solr_url = url
        self.solr = self._connect_to_solr()

    def _connect_to_solr(self):
        # establish the connection to Solr instance
        return pysolr.Solr(self.solr_url, auth=HTTPBasicAuth(SOLR_USERNAME, SOLR_PASSWORD), always_commit=True)

    def escape_query(self, raw_query):
        # Uncertain if this is really necessary
        return raw_query.replace("'", "\'")

    def delete_query(self, query, no_confirm=False):
        global SOLR_INSTANCE
        # execute delete query
        s = self.solr.search(self.escape_query(query), **{"rows": "0"})
        if s.hits == 0:
            print("No records found in " + SOLR_INSTANCE + " instance. Nothing to delete.  Exiting...")
        else:
            inMessage = "Are you sure you want to delete {num_recs} record(s) from " + SOLR_INSTANCE + " instance? Y/N: "
            are_you_sure = input(inMessage.format(num_recs=s.hits))
            if are_you_sure.lower() == "y":
                self.solr.delete(q=self.escape_query(query))
                confirmMessage = "Done deleting {num_recs} record(s) from " + SOLR_INSTANCE + " instance..."
                print(confirmMessage.format(num_recs=s.hits))
            else:
                print("Okay, nothing deleted from " + SOLR_INSTANCE + " instance. Exiting...")

    def json_to_dict(self, json_doc):
        # read data from one json file
        #print("Reading input file " + json_doc)
        j = json.load(open(json_doc, "rt", encoding="utf8"))      
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

    defaultPath = "R:\ARCHIVE_PROJECT\SCO_TEST\FinishedOpenMetadata\Eli_ReadyForIngest"

    def __init__(self, SOLR_USERNAME, SOLR_PASSWORD, FORCE, SCAN, COLLECTION, PROVENANCE, UUID, INSTANCE, TO_JSON=False, RECURSIVE=False, PURGE=False):
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

        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
        self.provenance = PROVENANCE
           
    def scan_dict_records(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True  
        d = list_of_dicts
        # Check if required elements have valid data       
        if(d["dc_identifier_s"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if(d["layer_slug_s"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if(d["dc_title_s"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if("NaN" in d["solr_geom"]):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if(d["dct_provenance_s"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if(d["dc_rights_s"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
        if(d["geoblacklight_version"] == ""):
            self.scanCatch.append(os.path.basename(self.currentFile))
       # if(d["solr_year_i"] == 9999):
        #   scanCatch += "solr_year_i\n"

        # If issues, print message and layer ids, set status to false
        if (len(self.scanCatch) != 0):
            status = False
            #print("\nQA health check failed for " + d["dc_title_s"] +
                  #"\nThe following fields are either missing data or have invalid entries: " + scanCatch) 
            # also send these result to a log file
        
        #print(d["layer_slug_s"] + "\n")
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
    

    def add(self, path_to_json):
        self.ingested = False
        #print("Add Single File Functionality still in Development")
        global SOLR_INSTANCE
        arg = (path_to_json.strip("\ "))
        if os.path.isfile(arg) and ".json" in arg:
            temp = "temp"
            if not os.path.exists(temp):
                os.mkdir(temp)
            file=os.path.basename(arg)
            newPath = temp+"/"+file
            shutil.copyfile(arg, newPath)
            self.force_add(temp)
            if self.success:
                os.remove(arg)
                print("No Files to Ingest")
            if self.ingested == True:
                #edit this to change where a file goes after it is successfully ingested
                os.rename(newPath,arg)
            shutil.rmtree(temp)   
        else:
            print("Argument is not a json. Please enter a valid file name.")
            
                   
    def force_add(self, path_to_json):
        global SOLR_INSTANCE
        self.scan(path_to_json)
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files and self.success == True:
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
            print("%i record(s) successfully ingested into Solr" % (len(self.dicts)))
            self.ingested = True
        elif self.success == False:
            print("Ingest Failed, Ingest Halted")
        elif not files:
            print("Ingest Failed, No Files to Ingest")
        else:
            print("Ingest Failed, Check JSON Location and Try Again") 

    def scan(self, path_to_json):
        self.success = False
        self.scanCatch = []
        # cycle through json files, add them to a dictionary object
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            cwd = os.getcwd()
            path = cwd + "\ for_review"
            self.dicts = []
            print("Performing QA scan...") 
            for i in files:
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                scanHold = self.scan_dict_records(dictAppend)
            print("QA health check failed on %i file(s): " % (len(self.scanCatch)))
            sortYN = input("Sort failed files into review folder and continue? (Y/N) ")
            if (scanHold == False and sortYN.upper()== "Y"):
                    try:
                        if os.path.exists(path):
                            print("Moving files to directory 'for_review'...")
                        else:
                            os.mkdir(path)
                            print("Creating directory 'for_review'...")
                            print("Moving files to directory 'for_review'...")
                        for file in self.scanCatch:
                            os.rename(path_to_json+ '/' +file, path + '/' + os.path.basename(file))
                        self.success = True
                        print( "%i record(s) successfully moved to 'for_review'" % (len(self.scanCatch)))
                    except OSError:
                        print("holup")
                        print("OS Failure")
            elif sortYN.upper() == "N":
                print("No Selected, Ingest Halted")
                self.success = False
            elif len(self.scanCatch) == 0:
                self.success = True
            else:
                print("Unrecognized Input, Scan Ended")
                self.success = False  
        else:
            print("No files found.  Exiting...")
            
	
    def delete(self, uuid):
        # setup query to delete a single record
        # the delete operation is handled by delete_query
        self.solr.delete_query("layer_slug_s:" + self.uuid)
        
    def delete_collection(self, collection):
        # setup query to delete an entire collection
        # print("Collection passed is: " + self.collection)
        self.solr.delete_query("dct_isPartOf_sm:" + '"' + self.collection + '"')
        
    def delete_provenance(self, provenance):
        # setup query to delete all records from specified provenance
        # print("Provenance passed is: " + self.provenance)
        self.solr.delete_query("dct_provenance_s:" + '"' + self.provenance + '"')  
        
    def purge(self):
        # setup query to purge all records from Solr
        self.solr.delete_query("*:*")

def main():
    defaultPath = "test-scenarios\eli-testdata"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--recursive",
        action='store_true',
        help="Recurse into subfolders when adding JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-afi",
        "--addFile",
        help="Indicate path to a GeoBlacklight JSON file")
    group.add_argument(
        "-afo",
        "--addFolder",
        help="Indicate path to folder with GeoBlacklight \
              #JSON files that will be uploaded.")
    group.add_argument(
        "-s",
        "--scan",
        help="Indicate path to folder with GeoBlacklight")
    group.add_argument(
        "-dc",
        "--delete-collection",
        help="Remove an entire collection from the Solr index.")  
    group.add_argument(
        "-dp",
        "--delete-provenance",
        help="Remove all records from Solr index that belong \
        to the specified provenance.")         
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
    interface = Update(SOLR_USERNAME, SOLR_PASSWORD, FORCE=args.addFolder, SCAN=args.scan, COLLECTION=args.delete_collection, PROVENANCE=args.delete_provenance, UUID=args.delete,INSTANCE=args.instance, RECURSIVE=args.recursive, PURGE=args.purge)
    
    inPath = args.addFile
    if (inPath is not None and inPath[-1] != '\\'):
            inPath += '\\'
    global SOLR_INSTANCE
    SOLR_INSTANCE = args.instance
    
    if args.addFile:
        interface.add(inPath)
    elif args.addFolder:
        interface.force_add(args.addFolder)
    elif args.scan:
        interface.scan(args.scan)
    elif args.delete_collection:
        interface.delete_collection(args.delete_collection)
    elif args.delete_provenance:
        interface.delete_provenance(args.delete_provenance)           
    elif args.delete:
        interface.delete(args.delete)
    elif args.purge:
        interface.purge()
    else:
        print("nothings happened")
        sys.exit(parser.print_help())

if __name__ == "__main__":
    sys.exit(main())
