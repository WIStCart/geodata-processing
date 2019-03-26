# Update.py
# Author: Ben Segal
# Description: script used for metadata transformations and parsing
# Dependencies: Python 3.x, lxml

isoxslt = '..\\xml_test_data\\xslt\\ArcGIS2ISO19139_uw-geodata.xsl'
jsonxslt = '..\\xml_test_data\\xslt\\iso2geoBL_uw-geodata.xsl'
import argparse
from os import listdir
from os.path import isfile, join
from shutil import copyfile
import os
import time

# Non standard python libraries
# requires additional installation
# lxml: py -m pip install lxml
import lxml.etree as ET

parser= argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Directory of input files')
parser.add_argument('-fi', '--input_format', help='Metadata format of input files')
parser.add_argument('-o', '--output', help='Directory for output files')
parser.add_argument('-fo', '--output_format', help='Metadata format for output files')
args = parser.parse_args()
inPath = args.input
outPath = args.output
count = 0

try:
    if (inPath[-1] != '\\'):
            inPath += '\\'
    if (outPath[-1] != '\\'):
        outPath += '\\'
    if ("\\" in inPath):
        inPath.replace("\\","\\\\")
    if ("\\" in outPath):
        outPath.replace("\\","\\\\")
    onlyfiles = [f for f in listdir(inPath) if (isfile(join(inPath, f)) and '.xml' in f)]

    def iso2gbl (xmlList, jsonxslt, ins, out):
        for xml in xmlList:
            if (args.input_format == 'esri'):
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
            if (args.input_format == 'esri'):
                os.remove(ins + filename + '_iso.xml')


    def esri2iso (xmlList, isoxslt, ins, out):
        for xml in onlyfiles:
            filename = xml[:-4]
            dom = ET.parse(ins + xml)
            xslt = ET.parse(isoxslt)
            transform = ET.XSLT(xslt)
            newdom = transform(dom)
            outfile = open(out + filename + '_iso.xml', 'w', encoding="utf-8")
            outfile.write(str(newdom))
            outfile.close()

    if (args.input_format == 'iso' and args.output_format == 'gbl'):
        iso2gbl(onlyfiles, jsonxslt, inPath, outPath)
    elif (args.input_format == 'esri' and args.output_format == 'iso'):
        esri2iso(onlyfiles, isoxslt, inPath, outPath)
    elif (args.input_format == 'esri' and args.output_format == 'gbl' ):
        esri2iso(onlyfiles, isoxslt, inPath, outPath)
        isofiles = [f for f in listdir(outPath) if (isfile(join(outPath, f)) and 'iso.xml' in f)]
        iso2gbl(isofiles, jsonxslt, outPath, outPath)
        

except TypeError:
    print("Ensure the input and output file paths and types are entered correctly.")