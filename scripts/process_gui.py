isoxslt = 'C:\\PROJECTS\\Directed_Studies\\XML_Test_Data\\xslt\\ArcGIS2ISO19139_uw-geodata.xsl'
jsonxslt = 'C:\\PROJECTS\\Directed_Studies\\XML_Test_Data\\xslt\\iso2geoBL_uw-geodata.xsl'
import argparse
from os import listdir
from os.path import isfile, join
from shutil import copyfile
import os
import lxml.etree as ET
import time
from Tkinter import *
import ttk
inForm = ''
window = Tk()
window.title("XML Transformer")
window.geometry('600x200')
lbl = Label(window, text="Input XML Filepath: ")
lbl.grid(column=0, row=0)
txtin = Entry(window,width=60)
txtin.grid(column=1, row=0)
lbl = Label(window, text=" ")
lbl.grid(column=0, row=1)
lbl = Label(window, text="Input Metadata format: ")
lbl.grid(column=0, row=2)
comboin = ttk.Combobox(window)
comboin['values']= ("Esri", "ISO19139")
comboin.current(0) #set the selected item
comboin.grid(column=1, row=2)
lbl = Label(window, text=" ")
lbl.grid(column=0, row=3)
lbl = Label(window, text="Output Filepath: ")
lbl.grid(column=0, row=4)
txtout = Entry(window,width=60)
txtout.grid(column=1, row=4)
lbl = Label(window, text="")
lbl.grid(column=0, row=5)
lbl = Label(window, text="Output Metadata format: ")
lbl.grid(column=0, row=6)
comboout = ttk.Combobox(window)
comboout['values']= ("ISO19139", "GBL (json)")
comboout.current(0) #set the selected item
comboout.grid(column=1, row=6)
lbl = Label(window, text=" ")
lbl.grid(column=0, row=7)
def clicked():
    inForm = comboin.get()
    inPath = txtin.get()
    outPath = txtout.get()
    outForm = comboout.get()
    window.destroy()
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
        print inPath
        print outPath
        def iso2gbl (xmlList, jsonxslt, ins, out):
            print('ISO19139 to GBL format:')
            for xml in xmlList:
                if (inForm == 'Esri'):
                    filename = xml[:-8]
                else:
                    filename = xml[:-4]
                data = open(jsonxslt)
                xslt_content = data.read()
                xslt_root = ET.XML(xslt_content)
                dom = ET.parse(ins + xml)
                transform = ET.XSLT(xslt_root)
                result = transform(dom)
                f = open(out + filename + '_gbl.json', 'w')
                f.write(str(result))
                f.close()
                if (inForm == 'Esri'):
                    os.remove(ins + filename + '_iso.xml')


        def esri2iso (xmlList, isoxslt, ins, out):
            print('Esri format to ISO19139:')
            for xml in onlyfiles:
                filename = xml[:-4]
                dom = ET.parse(ins + xml)
                xslt = ET.parse(isoxslt)
                transform = ET.XSLT(xslt)
                newdom = transform(dom)
                infile = unicode((ET.tostring(newdom, pretty_print=True)))
                outfile = open(out + filename + '_iso.xml', 'w')
                outfile.write(infile)

        if (inForm == 'ISO19139' and outForm == 'GBL (json)'):
            iso2gbl(onlyfiles, jsonxslt, inPath, outPath)
        elif (inForm == 'Esri' and outForm == 'ISO19139'):
            esri2iso(onlyfiles, isoxslt, inPath, outPath)
        elif (inForm == 'Esri' and outForm == 'GBL (json)' ):
            esri2iso(onlyfiles, isoxslt, inPath, outPath)
            isofiles = [f for f in listdir(outPath) if (isfile(join(outPath, f)) and 'iso.xml' in f)]
            iso2gbl(isofiles, jsonxslt, outPath, outPath)
            

    except TypeError:
        print("Ensure the input and output file paths and types are entered correctly.")
btn = Button(window, text="Submit", command=clicked)
btn.grid(column=1, row=8)
window.mainloop()

# parser= argparse.ArgumentParser()
# parser.add_argument('-i', '--input', help='Directory of input files')
# parser.add_argument('-fi', '--input_format', help='Metadata format of input files')
# parser.add_argument('-o', '--output', help='Directory for output files')
# parser.add_argument('-fo', '--output_format', help='Metadata format for output files')
# args = parser.parse_args()
# inPath = args.input
# outPath = args.output

