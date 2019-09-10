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
import simplejson
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
        # global SOLR_INSTANCE
        # execute delete query
        s = self.solr.search(self.escape_query(query), **{"rows": "0"})
        if s.hits == 0:
            print("No records found in " + SOLR_INSTANCE + " instance. Nothing to delete.  Exiting...")
        else:
            inMessage = "Are you sure you want to delete {num_recs} record(s) from " + SOLR_INSTANCE + " instance? (Y/N): "
            are_you_sure = input(inMessage.format(num_recs=s.hits))
            if are_you_sure.lower() == "y":
                self.solr.delete(q=self.escape_query(query))
                confirmMessage = "{num_recs} record(s) deleted from " + SOLR_INSTANCE + " instance."
                print(confirmMessage.format(num_recs=s.hits))
            else:
                print("Okay, nothing deleted from " + SOLR_INSTANCE + " instance. Exiting...")
                

    def json_to_dict(self, json_doc):
        # read data from one json file
        #print("Reading input file " + json_doc)
        try:
            j = json.load(open(json_doc, "rt", encoding="utf8"))
            return j
        except json.decoder.JSONDecodeError as err:
            json_name = os.path.basename(json_doc)
            print(" - {} has a syntax error at line {} column {}. Fix manually and reingest ".format(json_name,err.lineno, err.colno))
            exit()
        try:
            return j
        except UnboundLocalError:
            print("Fatal Syntax Error may effect the quality of this ingest")
        

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


    def __init__(self, SOLR_USERNAME, SOLR_PASSWORD, FORCE, SCAN, COLLECTION, PROVENANCE, UUID, INSTANCE, TO_JSON=False, RECURSIVE=False, PURGE=False):
        global SOLR_INSTANCE
        self.RECURSIVE = RECURSIVE
        self.PURGE = PURGE
        SOLR_INSTANCE = INSTANCE
        if INSTANCE=="prod":
            SOLR_URL = SOLR_URL_PRODUCTION
        elif INSTANCE=="test":
            SOLR_URL = SOLR_URL_TEST
        elif INSTANCE=="dev":
            SOLR_URL = SOLR_URL_DEV
        else: 
            # if instance not specified, default to dev
            print("Instance argument is null. Defaulting to dev...")
            print("Currently this is actually defaulting to test")
            SOLR_INSTANCE = "test"
            SOLR_URL = SOLR_URL_TEST

        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
        self.provenance = PROVENANCE
           
    def scan_dict_records(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True
        d = list_of_dicts
        # Check if required elements have valid data
        try:
            if(d["dc_identifier_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_identifier_s'")
            if(d["layer_slug_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'layer_slug_s'")
            if(d["layer_slug_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'layer_slug_s'")
            if("NaN" in d["solr_geom"]):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'solr_geom'")
            if(d["dct_provenance_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dct_provenance_s'")
            if(d["dc_rights_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_rights_s'")
            if(d["geoblacklight_version"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'geoblacklight_version'")
            if(d["dc_creator_sm"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_creator_sm'")
            if(d["dc_description_s"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_description_s'")
            if(d["dc_subject_sm"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_subject_sm'")
            if(d["solr_year_i"] == ""):
                #self.totalErrorNumbers = self.totalErrorNumbers + 1
                self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'solr_year_i'")
               # if(d["solr_year_i"] == 9999):
                #   scanCatch += "solr_year_i\n"
        except TypeError:
            print("QA Scan Error")
            #exit()
        
        # If issues, print message and layer ids, set status to false
        if (len(self.scanCatch) != 0):
            status = False
            #print("\nQA health check failed for " + d["dc_title_s"])
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
    
    def add_single(self, path_to_json):
        self.ingested = False
        arg = (path_to_json.strip("\ "))
        if os.path.isfile(arg) and ".json" in arg:
            temp = "temp"
            if not os.path.exists(temp):
                #print("creating directory temp...")
                os.mkdir(temp)
            # get name of file to be ingested
            file=os.path.basename(arg)
            newPath = temp+"/"+file
            # copy file to temporary folder 'temp'
            shutil.copyfile(arg, newPath)
            # run add_folder function to ingest file in folder 'temp'
            self.add_folder(temp)

            # delete file from original location so it's copy can be moved back after ingest
            if self.success and len(os.listdir(temp)) == 0:
                os.remove(arg)
                
            # move file back if necesary   
            if self.sortYN.upper() == "Y" and len(os.listdir(temp)) != 0:
                os.rename(newPath,arg)
            # delete temporary folder
            shutil.rmtree(temp)   
        else:
            print("File not found. Please enter a valid path to json")
            
                   
    def add_folder(self, path_to_json):
        self.scan(path_to_json)
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files and self.success == True:
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            if self.readyToIngest == True:
                confirm = input("Ingest file(s) into %s instance of Solr? (Y/N) " % SOLR_INSTANCE)
                if confirm.upper() == "Y":
                    ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
                    print("{} record(s) successfully ingested into {} instance of Solr".format(len(self.dicts), SOLR_INSTANCE))
                    self.ingested = True
                else:
                    print("Ingest terminated manually. Exiting...")

    def scan(self, path_to_json):
        global SOLR_INSTANCE
        if SOLR_INSTANCE == "":
            SOLR_INSTANCE = args.instance
            print("Solr Instance: %s" % SOLR_INSTANCE)
        self.success = False
        self.scanCatch = []
        self.fileProbList = []
        self.sortYN = ""
        #self.totalErrorNumbers = 0
        # cycle through json files, add them to a dictionary object
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            cwd = os.getcwd()
            path = cwd + "/for_review"
            self.dicts = []
            print("Performing QA scan...") 
            for i in files:
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                scanHold = self.scan_dict_records(dictAppend)
            if len(self.scanCatch) != 0:
                print("QA health check failed on {} file(s) ".format((len(self.scanCatch))))
                #print("QA health check failed on {} file(s) with {} total errors ".format((len(self.scanCatch)),self.totalErrorNumbers))
                print("-"*60)
                for bad_file in self.fileProbList:
                    print(" - "+ bad_file)
                print("-"*60)
                self.sortYN = input("Sort failed files into review folder and continue? (Y/N) ")
            else:
                print("QA Health Check Passed!")
                self.readyToIngest = True
            if (scanHold == False and self.sortYN.upper()== "Y"):
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
                        self.readyToIngest = True
                        print( "%i record(s) successfully moved to 'for_review'" % (len(self.scanCatch)))
                    except OSError:
                        print("OS Failure")
            elif self.sortYN.upper() == "N":
                print("Ingest terminated manually.  Exiting...")
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--recursive",
        action='store_true',
        help="Recurse into subfolders when adding JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-as",
        "--addSingleFile",
        help="Indicate path to a GeoBlacklight JSON file")
    group.add_argument(
        "-a",
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
    
    inPath = args.addSingleFile
    if (inPath is not None and inPath[-1] != '\\'):
            inPath += '\\'     
    if args.addSingleFile:
        interface.add_single(inPath)
    elif args.addFolder:
        interface.add_folder(args.addFolder)
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
        print("Nothings happened. Exiting...")
        sys.exit(parser.print_help())

if __name__ == "__main__":
    sys.exit(main())
