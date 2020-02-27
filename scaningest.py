"""
server_ingest.py
 
Author(s): Jim Lacy, Ben Segal, Eli Wilz
  
"""
import os
import time
import json
import argparse
import sys
from pathlib import Path
from collections import OrderedDict
from glob import glob
import fnmatch
import requests
from requests.auth import HTTPBasicAuth
from config import *

# non-standard Python libraries that require additional installation
# e.g., pip install pysolr
import pysolr
import shutil

class SolrInterface(object):

    def __init__(self, url=None):
        # init object and call Solr connection
        self.solr_url = url
        self.solr = self._connect_to_solr()

    def _connect_to_solr(self):
        # establish the connection to Solr instance
        return pysolr.Solr(self.solr_url, auth=HTTPBasicAuth(SOLR_USERNAME, SOLR_PASSWORD), always_commit=True)

    def escape_query(self, raw_query):
        return raw_query.replace("'", "\'")

    def delete_query(self, query, no_confirm=False):
        s = self.solr.search(self.escape_query(query), **{"rows": "0"})
        if s.hits == 0:
            print("No records found in " + SOLR_INSTANCE + " instance. Nothing to delete.")
        else:
            self.solr.delete(q=self.escape_query(query))
            confirmMessage = "{num_recs} record(s) deleted from " + SOLR_INSTANCE + " instance."
            print(confirmMessage.format(num_recs=s.hits))
                
    def json_to_dict(self, json_doc):
        # read data from one json file
        try:
            j = json.load(open(json_doc, "rt", encoding="utf8"))
            return j
        except json.decoder.JSONDecodeError as err:
            json_name = os.path.basename(json_doc)
            print(" - {} has a syntax error at line {} column {}. Fix manually and retry ".format(json_name,err.lineno, err.colno))
            exit()
        try:
            return j
        except UnboundLocalError:
            print("Syntax Error may effect the quality of this ingest")
        
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

    def __init__(self, SOLR_USERNAME, SOLR_PASSWORD, FOLDER, COLLECTION, INSTANCE):
        
        #grab instance from some other place, based on server?
        global SOLR_INSTANCE
        SOLR_INSTANCE = INSTANCE
        if INSTANCE=="prod":
            SOLR_URL = SOLR_URL_PRODUCTION
        elif INSTANCE=="test":
            SOLR_URL = SOLR_URL_TEST
        else: 
            SOLR_URL = SOLR_URL_TEST
        self.solr = SolrInterface(url=SOLR_URL)
        self.collection = COLLECTION
           
    def scan_dict_records(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True
        d = list_of_dicts
        # what is scancatch vs fileproblist
        try:
            if(("dc_identifier_s" not in d.keys()) or ((d["dc_identifier_s"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_identifier_s'")
            if(("layer_slug_s" not in d.keys()) or ((d["layer_slug_s"] == ""))):
                #currentErrorsList.append("layer_slug_s")
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'layer_slug_s'")
            if ((d["layer_slug_s"]) in self.uuidList):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' {} in 'layer_slug_s' already exists".format(d["layer_slug_s"]))  
            if("solr_geom" not in d.keys() or ("NaN" in d["solr_geom"])):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'solr_geom'")
            if(("dct_provenance_s" not in d.keys()) or ((d["dct_provenance_s"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dct_provenance_s'")
            if(("dc_rights_s" not in d.keys()) or ((d["dc_rights_s"] == ""))):
                #currentErrorsList.append("dc_rights_s")
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_rights_s'")
            if(("geoblacklight_version" not in d.keys()) or ((d["geoblacklight_version"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'geoblacklight_version'")
            if(("dc_creator_sm" not in d.keys()) or ((d["dc_creator_sm"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_creator_sm'")
            if(("dc_description_s" not in d.keys()) or ((d["dc_description_s"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_description_s'")
            #if(("dc_subject_sm" not in d.keys()) or ((d["dc_subject_sm"] == ""))):
            #    if os.path.basename(self.currentFile) not in self.scanCatch:
            #        self.scanCatch.append(os.path.basename(self.currentFile))
            #    self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field #'dc_subject_sm'")   
            if (("solr_year_i" not in d.keys()) or ((d["solr_year_i"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'solr_year_i'")
            self.uuidList.append(d["layer_slug_s"])
            
        except (KeyError,TypeError):
            print("QA Scan Error on file" + os.path.basename(self.currentFile))
            exit()
        
        # If issues, set status to false
        if (len(self.scanCatch) != 0):
            status = False

        return status
        
    def get_files_from_path(self, start_path, criteria="*"):
        # construct a list of json files to read
        # process fails if input directory contains a trailing \
        files = []
        for path, folder, ffiles in os.walk(start_path):
            for i in fnmatch.filter(ffiles, criteria):
                files.append(os.path.join(path, i))
        return files         
                   
    def add_folder(self, path_to_json):
        self.scan(path_to_json)
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        print(path_to_json)
        #print(files)
        if files and self.success == True:
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            if self.readyToIngest == True:
                print("Ingesting {} records(s) into Solr.".format(len(self.dicts)))
                ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
                print("{} record(s) successfully ingested into {} instance of Solr".format(len(self.dicts), SOLR_INSTANCE))
                self.ingested = True
    
    
    def scan(self, path_to_json):
        global SOLR_INSTANCE
        if SOLR_INSTANCE == "":
            SOLR_INSTANCE = args.instance
            print("Solr Instance: {}".format(SOLR_INSTANCE))
        self.success = False
        self.scanCatch = []
        self.fileProbList = []
        self.uuidList = []
        #self.fileErrorDict = {}
        self.sortYN = ""
        #print(self.fileErrorDict)
        #self.totalErrorNumbers = 0
        # cycle through json files, add them to a dictionary object
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            cwd = os.getcwd()
            path = Path(cwd,"for_review")
            self.dicts = []
            print("Performing QA scan...") 
            for i in files:
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                scanHold = self.scan_dict_records(dictAppend)
            if len(self.scanCatch) != 0:
                print("QA health check found {} error(s) in {} file(s) ".format((len(self.fileProbList)),len(self.scanCatch)))
                #print("QA health check failed on {} file(s) with {} total errors ".format((len(self.scanCatch)),self.totalErrorNumbers))
                print("-"*60)
                for bad_file in self.fileProbList:
                    print(" - "+ bad_file)
                print("-"*60)
                #for item in self.fileErrorDict.values():
                    #print(item)
                #print(self.fileErrorDict.values())
                self.sortYN = input("Sort {} failed files into review folder and continue? (Y/N) ".format((len(self.scanCatch))))
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
                            shutil.move(Path(path_to_json,file),Path(path,os.path.basename(file)))
                            #os.rename(Path(path_to_json,file),Path(path,os.path.basename(file)))
                            #print(Path(path_to_json,file))
                            #print(Path(path,os.path.basename(file)))
                        self.success = True
                        self.readyToIngest = True
                        print( "{} record(s) successfully moved to 'for_review'".format((len(self.scanCatch))))
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
    
    def delete_collection(self, collection):
        # setup query to delete an entire collection
        self.solr.delete_query("dct_isPartOf_sm:" + '"' + self.collection + '"')
       

def main():
    print("***********************************************************************")
    COLLECTION = "Wisconsin Open Data Sites"
    FOLDER = "d:\\projects\\geodata\\geodata-processing\\scanner\\"
    INSTANCE = "test"
    
    gblrecords = Update(SOLR_USERNAME, SOLR_PASSWORD, FOLDER, COLLECTION, INSTANCE)
    
    # Step 1 - Delete existing collection
    print("Deleting existing collection...")
    gblrecords.delete_collection(COLLECTION)

    # Step 2 - ingest updated GBL files
    print("Ingesting new files...")
    gblrecords.add_folder(FOLDER)


if __name__ == "__main__":
    sys.exit(main())
