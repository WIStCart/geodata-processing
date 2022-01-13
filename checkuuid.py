"""
checkuuid.py

Author(s): Jim Lacy
  
Description: 
Reads through files in specified folder(s) to find duplicate UUIDs.

Dependencies: Python 3.x
 
"""

import os
import json
import argparse
import sys
import collections
from glob import glob
import fnmatch

class Check(object):

    def __init__(self, FOLDER, RECURSIVE=False):
        self.RECURSIVE = RECURSIVE
              
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

    def json_to_dict(self, json_doc):
        # read data from one json file
        j = json.load(open(json_doc, "rt", encoding="utf8"))      
        return j
                    
    def checkFolder(self, path_to_json):
        files = self.get_files_from_path(path_to_json, criteria="*.json")
        # add contents of files to a dictionary object
        if files:
            self.dicts = []
            for i in files:
                dictAppend = self.json_to_dict(i)
                self.dicts.append(dictAppend)
        # add all uuids to uuid list
        uuidList = []
        for item in self.dicts:
            uuidList.append(item["layer_slug_s"])
        #look for duplicates
        seen = {}
        dupes = []
        for x in uuidList:
            if x not in seen:
                seen[x] = 1
            else:
                if seen[x] == 1:
                    dupes.append(x)
                seen[x] += 1
        # output results
        if dupes:
            print("\nDuplicate UUIDs found:")
            [print(i) for i in dupes]
                

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--recursive",
        action='store_true',
        help="Recurse into subfolders when adding JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-cf",
        "--checkFolder",
        help="Indicate path to folder with GeoBlacklight \
              JSON files that will be checked for duplicate uuid's.")               
    args = parser.parse_args()
    interface = Check(FOLDER=args.checkFolder, RECURSIVE=args.recursive)
       
    if args.checkFolder:
        interface.checkFolder(args.checkFolder)
    else:
        sys.exit(parser.print_help())

if __name__ == "__main__":
    sys.exit(main())
