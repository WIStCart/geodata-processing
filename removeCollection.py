"""
removeCollection.py
Author(s): Abby Gleason, Josh Seibel
  
Description: Remove specified "collection" from existing json file

Dependencies: Python 3.x
 
"""
import io
import os
import json
import argparse
import sys
from collections import OrderedDict

class CollectionRemove(object):
    def __init__(self, FOLDER, COLLECTION):
        self.FOLDER = FOLDER
        self.COLLECTION = COLLECTION    

    # Check for trailing backslash and remove
    def formatPath(self, folderPath):
        if folderPath[-1] == "\\":
            folderReady = folderPath[:-1]
        else:
            folderReady = folderPath
        return folderReady

    # Creates an output sub-folder if one does not already exist
    def createOutput(self, folderPath, collectionName):
        folderPath = self.formatPath(folderPath) + "\\output"
        
        # Create folder if doesn't exist
        if os.path.exists(folderPath):
            print("Output folder already exists.")

        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
            print("Output folder created.")   

    # Read through each json file and remove the specific collection
    def removeCollection(self, folderPath, collectionName):
        folderPath = self.formatPath(folderPath)

        for filename in os.listdir(folderPath):
            if filename.endswith(".json"): 
                jsonFile = json.load(io.open(folderPath + "\\" + filename, "rt", encoding="utf8"), object_pairs_hook=OrderedDict)
                self.checkExistingCollection(collectionName, filename, jsonFile)
                newFile = folderPath + "\\output\\" + filename
                with open (newFile, 'w') as outfile:
                    json.dump(jsonFile, outfile)

        print("Collection removed.")

    # Remove the collection name if it exists in file
    def checkExistingCollection(self, collectionName, filename, jsonFile):
        if collectionName in jsonFile["dct_isPartOf_sm"]:
            while collectionName in jsonFile["dct_isPartOf_sm"]:
                jsonFile["dct_isPartOf_sm"].remove(collectionName)
        else:
            print("Warning: Collection does not exist in file " + filename)
            return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--folderPath",
        help="Indicate path to folder to run script.")  
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c",
        "--collectionName",
        help="Remove specified collection from dct_isPartOf_sm.")         
    args = parser.parse_args()
    interface = CollectionRemove(FOLDER=args.folderPath, COLLECTION=args.collectionName)

    if (args.folderPath) and (args.collectionName):
        interface.createOutput(args.folderPath, args.collectionName)
        interface.removeCollection(args.folderPath, args.collectionName)
    else:
        sys.exit(parser.print_help())

if __name__ == "__main__":
    sys.exit(main())