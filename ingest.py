"""
Ingest.py

Author(s): Eli Wilz

Description:
This script is designed to sit on a server and automate the interactaction with a Solr instance running the GeoBlacklight 1.0 Schema.
1. Upload and and then ingest a directory of GBL-formatted json files. Optional: recurse into subfolders.
2. Delete a named "collection" from the Solr index
3. Delete a single record from the Index using the unique ID (uuid)
4. Delete all records from a specified repository (a.k.a. dct_provenance_s, a.k.a. "Held by")
5. Purge the entire Solr index.  The nuclear option!

When processing json inputs, the script performs some basic QA steps before the ingest is run.

All updates to Solr are "auto-committed" (changes are effective immediately)

Find Step-by-step descriptions of each function in the README File (this doesn't exist yet)

Dependencies: Python 3.x, pysolr, shutil

"""
import os
import json
import argparse
import sys
from pathlib import Path
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
            print("No records found in {} instance. Nothing to delete.  Exiting...".format(SOLR_INSTANCE))
        else:
            self.solr.delete(q=self.escape_query(query))
            print("NOTICE: {} record(s) deleted from {} instance.".format(s.hits,SOLR_INSTANCE))

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
            SOLR_INSTANCE = "dev"
            SOLR_URL = SOLR_URL_DEV

        self.solr = SolrInterface(url=SOLR_URL)
        self.uuid = UUID
        self.collection = COLLECTION
        self.provenance = PROVENANCE

    def qa_test(self, list_of_dicts):
        # perform QA checks on dictionary object before it is ingested
        status = True
        d = list_of_dicts
        # Add JSON Keys that are checked to see if they are null
        keyList = ["dc_identifier_s","layer_slug_s","solr_geom",
                    "dct_provenance_s","dc_rights_s","geoblacklight_version",
                    "dc_creator_sm","dc_description_s","solr_year_i"]
        # The QA Test
        try:
            for key in keyList:
                if((key not in d.keys()) or ((d[key] == ""))):
                    #print(key)
                    if os.path.basename(self.currentFile) not in self.failedFiles:
                        self.failedFiles.append(os.path.basename(self.currentFile))
                        self.stopIngest = True
        # Checks for Duplicate UUID already in Solr
            if(d["layer_slug_s"] not in self.uuidDict.values()):
                self.dupeUUID = str(d["layer_slug_s"])
                self.uuidDict.update({os.path.basename(self.currentFile): d["layer_slug_s"]})

        except (KeyError,TypeError):
            print("QA Scan Error on file" + os.path.basename(self.currentFile))
            exit()

        # If issues, print message and layer ids, set status to false
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
                    #files.append(os.path.join(path, i))
                    files.append(Path(path, i))
        else:
            files = Path(start_path).glob(criteria)
        return files

    def scan(self, path_to_json):
        ## sets up ingest
        ## creates variables and gets files to be ingested
        global SOLR_INSTANCE
        if SOLR_INSTANCE == "":
            SOLR_INSTANCE = args.instance
            print("Solr Instance: {}".format(SOLR_INSTANCE))
        self.failedFiles = []
        self.uuidDict = {}
        self.dupeUUID = ""
        self.stopIngest = False
        self.dupeCount = 0
        files = self.get_files_from_path(path_to_json, criteria="*.json")

        if files:
            self.dicts = []
            qaTestResult = False
            print("Performing QA scan...")
            for i in files:
                ## runs qa scan on files
                self.currentFile = i
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
                qaTestResult = self.qa_test(dictAppend)
            if len(self.dicts) == 0:
                print("ERROR: No Files Found, Use argument '-r' to ingest from subfolders")
                exit()

            elif self.stopIngest == True:
                print("QA test failed. One or more records has a  missing field. Exiting...")
                exit()

            else:
                ## runs duplicate uuid check
                self.uuid_overwrite(path_to_json)
                print("QA Health Check Passed!")
        else:
            print("No files found.  Exiting...")

    def add(self, path_to_json):
        ## adds files from folder
        ## stops if QA test fails
        self.scan(path_to_json)
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        if files:
            print("Preparing for Ingest. This may take a minute...")
            self.dicts = []
            for i in files:
                dictAppend = self.solr.json_to_dict(i)
                self.dicts.append(dictAppend)
            if len(self.dicts) != 0:
                print("Ingesting {} records(s) into Solr. This may take a minute...".format(len(self.dicts)))
                try:
                    ingest_result = self.solr.add_dict_list_to_solr(self.dicts)
                    print("{} record(s) successfully ingested into {} instance of Solr.".format(len(self.dicts), SOLR_INSTANCE))
                    self.ingested = True
                except OSError:
                    print("OS ERROR: Ingest Failed. Exiting...")
                    exit()
            else:
                print("Nothing to Ingest. Exiting...")
                exit()

        elif self.stopIngest == True:
            print("QA Test Failed.")
            print("Exiting...")
            exit()

    def uuid_overwrite(self, path_to_json):
        ## checks for duplicate uuids being uploaded
        ## automatically overwrites old records with new ones
        print("Checking for duplicate UUIDs...")
        self.ingestingDict = {}
        self.inSolrDict = {}
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        for file in files:
            uuidDict = self.solr.json_to_dict(file)
            uuid = uuidDict["layer_slug_s"]
            self.ingestingDict[uuid] = str(os.path.basename(file))
            results = self.solr.uuid_scan(uuid)
            for result in results:
                re_uuid = result["layer_slug_s"]
                self.inSolrDict[re_uuid] = str(os.path.basename(file))

            if uuid in self.inSolrDict.keys():
                self.dupeCount = self.dupeCount + 1

        if self.dupeCount != 0:
            print("NOTICE: Overwriting {} records where UUID is associated with an existing record in Solr.".format(str(self.dupeCount)))

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
        "-a",
        "--add",
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
    interface = Update(SOLR_USERNAME, SOLR_PASSWORD, FORCE=args.add, SCAN=args.scan, COLLECTION=args.delete_collection, PROVENANCE=args.delete_provenance, UUID=args.delete,INSTANCE=args.instance, RECURSIVE=args.recursive, PURGE=args.purge)

    inPath = args.add
    if (inPath is not None and inPath[-1] != '\\'):
            inPath += '\\'
    if args.add:
        interface.add(args.add)
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
