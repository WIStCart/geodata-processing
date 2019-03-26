# Update.py
# Author: Ben Segal
# Description: script used for metadata transformations and parsing
# Dependencies: Python 3.x, lxml
isoxslt = '..\\XML_Test_Data\\xslt\\ArcGIS2ISO19139_uw-geodata.xsl'
jsonxslt = '..\\XML_Test_Data\\xslt\\iso2geoBL_uw-geodata.xsl'

# Standard python packages
import argparse
from os import listdir
from os.path import isfile, join
import os

# Non standard python libraries
# requires additional installation
# lxml: py -m pip install lxml
import lxml.etree as ET

# Establish input directory and metadata types for data transformations
parser= argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Directory of input files')
parser.add_argument('-fi', '--input_format', help='Metadata format of input files', required=False, choices={"esri", "Esri","ESRI", "iso", "ISO"})
parser.add_argument('-o', '--output', help='Directory for output files')
parser.add_argument('-fo', '--output_format', help='Metadata format for output files', required=False, choices={"iso", "ISO", "gbl", "GBL"})
args = parser.parse_args()
inPath = args.input
outPath = args.output
inForm = args.input_format
outForm = args.output_format

# Set file types if user leaves these options blank
if (inForm is None):
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
            gblCount += 1
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
            outfile = open(out + filename + '_iso.xml', 'w', encoding="utf-8")
            outfile.write(str(newdom))
            outfile.close()
            isoCount += 1
        if (outForm == 'iso' or outForm == 'ISO'):
            print (str(isoCount) + " records transformed from " + inForm + " to " + outForm)

    # Run transformations based on input file types
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