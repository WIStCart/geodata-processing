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

- Create UUID Filter on Duplicate UUIDs

- Develop UI or GUI


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

    def uuid_scan(self, uuid):
        results = self.solr.search(uuid)
        return results



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
            #print("Currently this is actually defaulting to test")
            SOLR_INSTANCE = "test"
            SOLR_URL = SOLR_URL_TEST

        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
        self.provenance = PROVENANCE

    def qa_test(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True
        d = list_of_dicts
        # Check if required elements have valid data
        try:
            if(("dc_identifier_s" not in d.keys()) or ((d["dc_identifier_s"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_identifier_s'")
            if(("layer_slug_s" not in d.keys()) or ((d["layer_slug_s"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'layer_slug_s'")
            if ((d["layer_slug_s"]) in self.uuidDict.values()):
                self.dupeUUID = str(d["layer_slug_s"])
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
            # if(("dc_subject_sm" not in d.keys()) or ((d["dc_subject_sm"] == ""))):
            #     if os.path.basename(self.currentFile) not in self.scanCatch:
            #         self.scanCatch.append(os.path.basename(self.currentFile))
            #     self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'dc_subject_sm'")
            # if (("solr_year_i" not in d.keys()) or ((d["solr_year_i"] == ""))):
                if os.path.basename(self.currentFile) not in self.scanCatch:
                    self.scanCatch.append(os.path.basename(self.currentFile))
                self.fileProbList.append("File '" + os.path.basename(self.currentFile)+ "' has null field 'solr_year_i'")
               # if(d["solr_year_i"] == 9999):
                #   scanCatch += "solr_year_i\n"
            #self.uuidList.append(d["layer_slug_s"])
            self.uuidDict.update({os.path.basename(self.currentFile): d["layer_slug_s"]})



        except (KeyError,TypeError):
            print("QA Scan Error on file" + os.path.basename(self.currentFile))
            exit()
        # Testing using a dictionary to hold errors instead
        #if currentErrorsList:
            #self.fileErrorDict.update({self.currentFile:currentErrorsList})

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
                    files.append(Path(path, i))
        else:
            #files = glob(os.path.join(start_path, criteria))
            files = Path(start_path).glob(criteria)
        return files

    def add_single(self, path_to_json):
        self.ingested = False
        arg = (path_to_json.strip("\\"))
        if os.path.isfile(arg) and ".json" in arg:
            temp = "temp"
            if not os.path.exists(temp):
                os.mkdir(temp)
            # get name of file to be ingested
            file=os.path.basename(arg)
            newPath = Path(temp,file)
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
            print("File not found. Please enter a valid path to a single json file")


    def add_folder(self, path_to_json):
        self.scan(path_to_json)
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files and self.success == True:
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            if self.readyToIngest == True and len(self.dicts) != 0:
                if len(self.dicts) == 0:
                    print("All Files Moved to 'for_review', Nothing to Ingest")
                else:
                    print("Preparing for ingest. This may take a minute...")
                    confirm = input("Ingest {} file(s) into {} instance of Solr? (Y/N) ".format((len(self.dicts)),SOLR_INSTANCE))
                    if confirm.upper() == "Y":
                        print("Ingesting {} records(s) into Solr. This may take a minute...".format(len(self.dicts)))
                        ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
                        print("{} record(s) successfully ingested into {} instance of Solr".format(len(self.dicts), SOLR_INSTANCE))
                        self.ingested = True
                    else:
                        print("Ingest terminated manually. Exiting...")

    def uuid_overwrite(self, path_to_json):
        exists = False
        print("Checking for duplicate UUIDs. This may take a minute...")
        self.ingestingDict = {}
        self.inSolrDict = {}
        self.recordCount = int(len(self.dicts))
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        apply_all_flag = False
        counter = int(len(self.dicts)-1)
        for file in files:
            #self.ingestingList.append(os.path.basename(file))
            uuidDict = self.solr.json_to_dict(file)
            uuid = uuidDict["layer_slug_s"]
            self.ingestingDict[uuid] = str(os.path.basename(file))
            results = self.solr.uuid_scan(uuid)
            for result in results:
                re_uuid = result["layer_slug_s"]
                re_title = result["dc_title_s"]
                self.inSolrDict[re_uuid] = str(os.path.basename(file))

            if uuid in self.inSolrDict.keys() and apply_all_flag == False:
                inSolrDupe = self.inSolrDict[uuid]
                ingestingDupe = self.ingestingDict[uuid]
                self.dupeCount = self.dupeCount + 1
                print("-"*45)
                print(" - File '{}' has a UUID that is already associated with a record in Solr: '{}'".format(ingestingDupe,re_title))
                print("-"*45)
                overwrite = input("Overwrite existing record '{}'? or type 'All' to overwrite {} remaining record(s) (Y/N/A) ".format(re_title, self.recordCount))
                if overwrite.upper() == "N" or overwrite.upper() == "NO":
                    move = input("Move {} to 'for_review' folder and continue processing? (Y/N) ".format(ingestingDupe))
                    if move.upper() == "Y":
                        self.recordCount = (self.recordCount - 1)
                        print("PATH: " + str(self.path))
                        print("PATHTOJSON: " + str(path_to_json))
                        folders = [f.name for f in os.scandir(path_to_json) if f.is_dir()]
                        for folder in folders:
                            recursivePath = Path(path_to_json,folder)
                            recursiveReview = Path(recursivePath,"for_review")
                            print(recursivePath)
                            print(recursiveReview)
                            print("MOVE FROM: " + str(Path(recursivePath,os.path.basename(file))))
                            print("MOVE TO: " + str(recursiveReview))
                            if not os.path.exists(self.path):
                                os.mkdir(self.path)
                            shutil.move(Path(recursivePath,os.path.basename(file)),Path(self.path,os.path.basename(file)))
                    elif move.upper() == "N":
                        print("Ingest terminated manually.  Exiting...")
                        exit()
                    else:
                        print("Unrecognized Command, Exiting...")
                        exit()
                elif overwrite.upper() == "Y" or overwrite.upper() =="YES":
                    apply_all_flag = False
                elif overwrite.upper() == "A" or overwrite.upper() == "ALL":
                    apply_all_flag = True
                else:
                    print("Unrecognized Command, Exiting...")
                    exit()
            elif uuid in self.inSolrDict.keys():
                pass

        #if self.dupeCount != 0:
            #print("NOTICE: Overwriting {} records where UUID is associated with an existing record in Solr.".format(str(self.dupeCount)))

        print("UUID Health Check Complete")

    def scan(self, path_to_json):
        global SOLR_INSTANCE
        if SOLR_INSTANCE == "":
            SOLR_INSTANCE = args.instance
            print("Solr Instance: {}".format(SOLR_INSTANCE))
        self.success = False
        self.scanCatch = []
        self.fileProbList = []
        self.uuidDict = {}
        self.sortYN = ""
        self.dupeUUID = ""
        self.dupeCount = 0
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            cwd = os.getcwd()
            #change where 'for_review' folder gets created
            self.path = Path(path_to_json,"for_review")
            self.dicts = []
            print("Performing QA scan...")
            qaTestResult = False
            for i in files:
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                qaTestResult = self.qa_test(dictAppend)
            if len(self.scanCatch) != 0:
                if len(self.uuidDict) > 1:
                    for item in self.uuidDict.keys():
                        if self.uuidDict[item] == self.dupeUUID:
                            if item not in self.scanCatch:
                                self.scanCatch.append(item)
                            self.fileProbList.append("File '{}' has duplicate UUID: '{}' ".format(item, self.dupeUUID))
                print("QA health check found {} error(s) in {} file(s) ".format((len(self.fileProbList)),len(self.scanCatch)))
                print("-"*60)
                for bad_file in self.fileProbList:
                    print(" - "+ bad_file)
                print("-"*60)
                self.sortYN = input("Sort {} failed files into review folder and continue? (Y/N) ".format((len(self.scanCatch))))
            else:
                self.uuid_overwrite(path_to_json)
                print("QA Health Check Passed!")
                self.readyToIngest = True
            if (qaTestResult == False and self.sortYN.upper()== "Y"):
                    try:
                        if os.path.exists(self.path):
                            print("Moving files to directory 'for_review'...")
                        else:
                            os.mkdir(path)
                            print("Creating directory 'for_review'...")
                            print("Moving files to directory 'for_review'...")
                        for file in self.scanCatch:
                            if not os.path.exists(self.path):
                                os.mkdir(self.path)
                            shutil.move(Path(path_to_json,file),Path(self.path,os.path.basename(file)))
                        self.success = True
                        self.readyToIngest = True
                        print( "{} record(s) successfully moved to 'for_review'".format((len(self.scanCatch))))
                        self.uuid_overwrite(path_to_json)
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
