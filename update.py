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

- create a README
- decide what should maintain in repository



"""

import os
import json
import argparse
import sys
from pathlib import Path
from glob import glob
import fnmatch
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
        num_recs = s.hits
        if s.hits == 0:
            print("No records found in {} instance. Nothing to delete.  Exiting...".format(SOLR_INSTANCE))
        else:
            inMessage = "Are you sure you want to delete {} record(s) from {} instance? (Y/N): ".format(num_recs,SOLR_INSTANCE)
            are_you_sure = input(inMessage.format(num_recs))
            if are_you_sure.lower() == "y":
                self.solr.delete(q=self.escape_query(query))
                print("{} record(s) deleted from {} instance.".format(num_recs,SOLR_INSTANCE))
            else:
                print("Okay, nothing deleted from {} instance. Exiting...".format(SOLR_INSTANCE))


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
            SOLR_INSTANCE = "dev"
            SOLR_URL = SOLR_URL_TEST

        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
        self.provenance = PROVENANCE

    def qa_test(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True
        d = list_of_dicts
        file = os.path.basename(self.currentFile)
        uuid = d["layer_slug_s"]

        # Add JSON Keys that are checked to see if they are null
        keyList = ["dc_title_s", "dc_identifier_s","layer_slug_s","solr_geom",
                    "dct_provenance_s","dc_rights_s","geoblacklight_version",
                    "dc_creator_sm","dc_description_s","solr_year_i"]

        # Check if required elements have valid data
        # The QA Test
        try:
            for key in keyList:
                if (key not in d.keys()) or ((d[key] == "")) or d[key] == ['']:
                    if os.path.basename(self.currentFile) not in self.failedFiles:
                        self.failedFiles.append(file)
                    self.fileProbList.append("File '{}' has null field '{}'".format(file,key))

            if uuid not in self.dupeDict.values():
                self.dupeDict.update({file : uuid})
            else:
                key_list = list(self.dupeDict.keys())
                val_list = list(self.dupeDict.values())
                dupe_file = key_list[val_list.index(uuid)]
                print("-"*45)
                print(" ERROR: Attempting to upload Duplicate UUIDs.")
                print("-"*45)
                print(" - Files '{}' and '{}' have the same UUID: '{}'".format(file,dupe_file,uuid))
                print("-"*45)
                print("Exiting...")
                exit()

        except (KeyError,TypeError):
            print("QA Scan Error on file {}".format(os.path.basename(self.currentFile)))
            exit()

        # If a file has failed, switch the status to False
        if (len(self.failedFiles) != 0):
            status = False
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
            files = Path(start_path).glob(criteria)
        return files

    def scan(self, path_to_json):
        global SOLR_INSTANCE
        if SOLR_INSTANCE == "":
            SOLR_INSTANCE = args.instance
            print("Solr Instance: {}".format(SOLR_INSTANCE))
        self.success = False
        self.dupeDict = {}
        self.failedFiles = []
        self.fileProbList = []
        self.uuidDict = {}
        self.sortYN = ""
        self.dupeUUID = ""
        folders = [f.name for f in os.scandir(path_to_json) if f.is_dir()]
        if len(folders) >= 2:
            self.isRecursive = True
        else:
            self.isRecursive = False
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            cwd = os.getcwd()
            #change where 'for_review' folder gets created
            self.path = Path(path_to_json,"for_review")
            self.dicts = []
            self.recordCount = int(len(self.dicts))
            print("Performing QA scan...")
            qaTestResult = False
            for i in files:
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                qaTestResult = self.qa_test(dictAppend)
            if len(self.dicts) == 0:
                print("ERROR: No Files Found, Use argument '-r' to ingest from subfolders")
                exit()

            if len(self.failedFiles) != 0:
                print("QA health check found {} error(s) in {} file(s) ".format((len(self.fileProbList)),len(self.failedFiles)))
                print("-"*60)
                for bad_file in self.fileProbList:
                    print(" - {}".format(bad_file))
                print("-"*60)
                self.sortYN = input("Sort {} failed files into review folder and continue? (Y/N) ".format((len(self.failedFiles))))
            else:
                self.uuid_overwrite(path_to_json)
                self.readyToIngest = True
                if self.recordCount == 0:
                    print("NOTICE: All records moved to 'for_review'. Nothing to ingest. Exiting...")
                    exit()
                else:
                    if len(self.inSolrDict) != 0:
                        print("NOTICE: Overwriting {} records where UUID is associated with an existing record in Solr.".format(self.recordCount))
                    print("QA Health Check Passed!")
            if (qaTestResult == False and self.sortYN.upper()== "Y"):
                    try:
                        if os.path.exists(self.path):
                            print("Moving files to directory 'for_review'...")
                        else:
                            os.mkdir(self.path)
                            print("Creating directory 'for_review'...")
                            print("Moving files to directory 'for_review'...")
                        for file in self.failedFiles:
                            if not os.path.exists(self.path):
                                os.mkdir(self.path)
                            self.recordCount = (self.recordCount - 1)
                            shutil.move(Path(path_to_json,file),Path(self.path,os.path.basename(file)))
                        self.success = True
                        self.readyToIngest = True
                        print( "{} record(s) successfully moved to 'for_review'".format((len(self.failedFiles))))
                        self.uuid_overwrite(path_to_json)
                    except OSError:
                        print("OS Failure")
            elif self.sortYN.upper() == "N":
                print("Ingest terminated manually.  Exiting...")
                self.success = False
            elif len(self.failedFiles) == 0:
                self.success = True
            else:
                print("Unrecognized Input, Scan Ended")
                self.success = False
        else:
            print("No files found.  Exiting...")

    def add_single(self, path_to_json):
        self.ingested = False
        arg = (path_to_json.strip("\\"))
        file=os.path.basename(arg)
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
        try:
            self.scan(path_to_json)
        except FileNotFoundError:
            print("ERROR: Not a valid file path.")
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files and self.success == True:
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            if self.readyToIngest == True and len(self.dicts) != 0:
                self.ingestCount = (self.recordCount-(len(self.failedFiles)))
                if len(self.dicts) == 0:
                    print("All Files Moved to 'for_review', Nothing to Ingest")
                else:
                    print("Preparing for ingest. This may take a minute...")
                confirm = input("Ingest {} file(s) into {} instance of Solr? (Y/N) ".format(self.ingestCount,SOLR_INSTANCE))

                if confirm.upper() == "Y":
                    print("Ingesting {} records(s) into Solr. This may take a minute...".format(self.ingestCount))
                    ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
                    print("{} record(s) successfully ingested into {} instance of Solr.".format(self.ingestCount,SOLR_INSTANCE))
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
        for file in files:
            self.uuidDict = self.solr.json_to_dict(file)
            uuid = self.uuidDict["layer_slug_s"]
            self.ingestingDict[uuid] = str(os.path.basename(file))
            results = self.solr.uuid_scan(uuid)
            for result in results:
                re_uuid = result["layer_slug_s"]
                re_title = result["dc_title_s"]
                self.inSolrDict[re_uuid] = str(os.path.basename(file))

            if uuid in self.inSolrDict.keys() and apply_all_flag == False:
                inSolrDupe = self.inSolrDict[uuid]
                ingestingDupe = self.ingestingDict[uuid]
                print("")
                print("-"*45)
                print(" - File '{}' has a UUID that is already associated with a record in Solr: '{}'".format(ingestingDupe,re_title))
                print("-"*45)
                self.DIRLEN = (len([name for name in os.listdir(path_to_json) if os.path.isfile(os.path.join(path_to_json, name))]))
                if self.isRecursive == True:
                    print(" ")
                    overwrite = input("Overwrite existing record '{}'? or type '(A)ll' to overwrite {} remaining record(s) (Y/N/A) ".format(re_title, self.recordCount))
                if self.isRecursive == False:
                    overwrite = input("Overwrite existing record '{}'? or type '(A)ll' to overwrite {} remaining record(s) (Y/N/A) ".format(re_title, self.DIRLEN))
                if overwrite.upper() == "N" or overwrite.upper() == "NO":
                    move = input("Move {} to 'for_review' folder and continue processing? (Y/N) ".format(ingestingDupe))
                    if move.upper() == "Y":
                        self.recordCount = (self.recordCount - 1)
                        folders = [f.name for f in os.scandir(path_to_json) if f.is_dir()]
                        if len(folders) >= 2:
                            for folder in folders:
                                moveSource = Path(Path(path_to_json,folder),ingestingDupe)
                                moveDestination = Path(Path(path_to_json,"for_review"),ingestingDupe)
                                try:
                                    if not os.path.exists(self.path):
                                        os.mkdir(self.path)
                                except OSError:
                                    print("OS ERROR")
                                try:
                                    shutil.move(moveSource,moveDestination)
                                except FileNotFoundError:
                                    pass
                        else:
                            if not os.path.exists(self.path):
                                os.mkdir(self.path)
                            moveSource = Path(path_to_json,os.path.basename(file))
                            moveDestination = Path(self.path,os.path.basename(file))
                            shutil.move(moveSource,moveDestination)

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
        self.DIRLEN = (len([name for name in os.listdir(path_to_json) if os.path.isfile(os.path.join(path_to_json, name))]))

    def delete(self, uuid):
        # setup query to delete a single record
        # the delete operation is handled by delete_query
        self.solr.delete_query("layer_slug_s:{}".format(self.uuid))

    def delete_collection(self, collection):
        # setup query to delete an entire collection
        self.solr.delete_query('dct_isPartOf_sm:"{}"'.format(self.collection))

    def delete_provenance(self, provenance):
        # setup query to delete all records from specified provenance
        self.solr.delete_query("dct_provenance_s:{}".format(self.provenance))

    def purge(self):
        # setup query to purge all records from Solr
        self.solr.delete_query("*:*")

def main():
    print('-'*45)
    print(" "*10+"- Update version 3.0 -")
    print('-'*45)
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
    group = parser.add_mutually_exclusive_group(required=True)
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
