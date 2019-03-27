# Update.py
# Author: Ben Segal
# Description: script used for metadata transformations and parsing
# Dependencies: Python 3.x, lxml

###### I updated xslt paths to reference copies that sit on Jaime's server
###### moving forward let's use this path.  You should have an R: drive now... see slack
isoxslt = 'R:\\SCRIPTS\\xslt\\ArcGIS2ISO19139_uw-geodata.xsl'
jsonxslt = 'R:\\SCRIPTS\\xslt\\iso2geoBL_uw-geodata.xsl'

# Standard python packages
import argparse
from os import listdir
from os.path import isfile, join
import os

# Non standard python libraries
# requires additional installation
# lxml: py -m pip install lxml

###### is py versus python as standard thing?  "py" does not work on my computer.
###### I had to edit process.bat to get things working on my PC
import lxml.etree as ET

# Establish input directory and metadata types for data transformations

##### take a second look at how you are handling the arguments
##### when no output is provided, I would expect to see something akin to the following (example):

"""

usage: update.py [-h] [-r]
                 (-aj ADD_JSON | -dc DELETE_COLLECTION | -d DELETE | -p)
                 [-i {test,prod,dev}]
update.py: error: one of the arguments -aj/--add-json -dc/--delete-collection -d/--delete -p/--purge is required

"""

###### take a look at the argument handling in update.py for some ideas.


parser= argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Directory of input files')
parser.add_argument('-fi', '--input_format', help='Metadata format of input files', required=False, choices={"esri", "Esri","ESRI", "iso", "ISO"})
parser.add_argument('-o', '--output', help='Directory for output files')
parser.add_argument('-fo', '--output_format', help='Metadata format for output files', required=False, choices={"iso", "ISO", "gbl", "GBL"})
########## No need to handle multiple combinations of case.. iso, ISO, Esri, ESRI, etc.  Just convert everything to lowercase after input is received.  I think the syntax is stringname.lower()????
args = parser.parse_args()
inPath = args.input
outPath = args.output
inForm = args.input_format
outForm = args.output_format

# Set file types if user leaves these options blank
if (inForm is None):
    ###### actually this should be iso not esri
    inForm = 'esri'
if (outForm is None):
    outForm = 'gbl'

try:
    if (inPath[-1] != '\\'):
            inPath += '\\'
    if (outPath[-1] != '\\'):
        outPath += '\\'
    if ("\\" in inPath):
        inPath.replace("\\","\\\\")
    if ("\\" in outPath):
        outPath.replace("\\","\\\\")
    
    # Create list of all files that end in .xml in input file directory
    onlyfiles = [f for f in listdir(inPath) if (isfile(join(inPath, f)) and '.xml' in f)]

    # Transform ISO 19139 metadata to json format
    def iso2gbl (xmlList, jsonxslt, ins, out):
        gblCount = 0
        for xml in xmlList:
            if (inForm == 'esri' or inForm == 'Esri' or inForm == 'ESRI'):
                filename = xml[:-8]
            else:
                filename = xml[:-4]
            data = open(jsonxslt)
            xslt_content = data.read()
            xslt_root = ET.XML(xslt_content)
            dom = ET.parse(ins + xml)
            transform = ET.XSLT(xslt_root)
            result = transform(dom)
            f = open(out + filename + '.json', 'w', encoding="utf-8")
            f.write(str(result))
            f.close()
            ######## suggest writing out the filename as output is created.  This helps the user know that something is happening.
            gblCount += 1
            ######## instead of going thru all of the follow tests, just convert the input to all lower case. This will greatly simplify some of the statements below.
            
            ##### also, new information: turns out we should save the _iso file that is created as part of the process.  So you can remove the following
            
            if (inForm == 'esri' or inForm == 'Esri' or inForm == 'ESRI'):
                os.remove(ins + filename + '_iso.xml')
        print (str(gblCount) + " records transformed from " + inForm + " to " + outForm)

    # Transform esri metadata to ISO 19139 format
    def esri2iso (xmlList, isoxslt, ins, out):
        isoCount = 0
        for xml in onlyfiles:
            filename = xml[:-4]
            dom = ET.parse(ins + xml)
            xslt = ET.parse(isoxslt)
            transform = ET.XSLT(xslt)
            newdom = transform(dom)
            ####### same comments as above, print out an indication of what's being processed so the user knows something is happening
            outfile = open(out + filename + '_iso.xml', 'w', encoding="utf-8")
            outfile.write(str(newdom))
            outfile.close()
            isoCount += 1
        if (outForm == 'iso' or outForm == 'ISO'):
            print (str(isoCount) + " records transformed from " + inForm + " to " + outForm)

    # Run transformations based on input file types
    
    
    ###### what happens if the user inputs an invalid combination of -fi and -fo? eg., -fi gbl -fo esri, -fi iso -fo esri, -fi iso -fo iso etc.  Try some combos.  Hint: more error checking needed.
    
    #######  see comments above about converting all input to lowercase.  
    
    if ((inForm == 'iso' or inForm == 'ISO') and (outForm == 'gbl' or outForm == 'GBL')):
        iso2gbl(onlyfiles, jsonxslt, inPath, outPath)
    elif ((inForm == 'esri' or inForm == 'Esri' or inForm == 'ESRI') and (outForm == 'iso' or outForm == 'ISO')):
        esri2iso(onlyfiles, isoxslt, inPath, outPath)
    elif ((inForm == 'esri' or inForm == 'Esri' or inForm == 'ESRI') and (outForm == 'gbl' or outForm == 'GBL')):
        esri2iso(onlyfiles, isoxslt, inPath, outPath)
        isofiles = [f for f in listdir(outPath) if (isfile(join(outPath, f)) and 'iso.xml' in f)]
        iso2gbl(isofiles, jsonxslt, outPath, outPath)
        

except TypeError:
    print("Ensure the input and output file paths and types are entered correctly.")