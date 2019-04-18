"""
esriscanner.py

Author(s): Ben Segal

Description: 
This script is designed to run every day, and convert arcgis json records to GBL records.


Dependencies: Python 3.x
"""
import json
import urllib.request
from html.parser import HTMLParser
import shutil
import os

shutil.rmtree('C:/PROJECTS/Directed_Studies/esriscanner/data-ltsb')
shutil.rmtree('C:/PROJECTS/Directed_Studies/esriscanner/data-wi-dnr')
os.makedirs('C:/PROJECTS/Directed_Studies/esriscanner/data-ltsb')
os.makedirs('C:/PROJECTS/Directed_Studies/esriscanner/data-wi-dnr')


# Strip html from description
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

# Create GBL records from LTSB data
# open and read data.json
s = urllib.request.urlopen("https://data-ltsb.opendata.arcgis.com/data.json").read()
d = json.loads(s.decode('utf-8'))
with open('C:\\PROJECTS\\Directed_Studies\\esriscanner\\test.json', 'w') as fout:
    json.dump(d, fout, indent=1)
# loop through each record
for x in d["dataset"]:
    # call html strip function
    description = strip_tags(x["description"]).replace('Attribute Field Definitions', '')
    access = x["accessLevel"].capitalize()
    envelope = "ENVELOPE(" + x["spatial"] + ")"
    identifier = x["identifier"]
    # create slug from end of identifier and 'LTSB_OpenData_'
    slug = "LTSB_OpenData_" + x["identifier"].replace('http://data-ltsb.opendata.arcgis.com/datasets/','')
    mod = x["modified"]
    geomType = ""
    # grab raw metadata if available and get geom type
    if("FeatureServer" in x["webService"]):
        a = urllib.request.urlopen(x["webService"] + "?f=pjson").read()
        b = json.loads(a.decode('utf-8'))
        geomType = b["geometryType"].replace('esriGeometry', '')
    # create references from distribution 
    references = "{"
    for t in x["distribution"]:
        if 'downloadURL' in t:
            references += '\"http://schema.org/downloadUrl\":\"' + t["downloadURL"] + '\",'
    references += '\"http://schema.org/url\":\"' + x["identifier"] + '\",'
    references += "}"
    references = references.replace(",}", "}")
    # format gbl record
    temp_obj = {
        "geoblacklight_version": "1.0",
        "dc_identifier_s": identifier,
        "dc_title_s": x["title"],
        "dc_description_s": description,
        "dc_rights_s": access,
        "dct_provenance_s": x["publisher"]["name"],
        "layer_id_s": "", # leave blank? 
        "layer_slug_s": slug,
        "layer_geom_type_s": geomType, # type not in data.json
        "layer_modified_dt": x["modified"],
        "dc_format_s": "Shapefile", # all esri sites so probably shapefile?
        "dc_language_s": "English",
        "dct_isPartOf_sm": "Wisconsin Legislative Technology Services Bureau Open Data",
        "dc_creator_sm": x["publisher"]["name"],
        "dc_type_s": "Dataset",
        "dc_subject_sm": x["keyword"],
        "dct_spatial_sm": "", # no spatial field in data.json
        "dct_issued_s": x["issued"],
        "dct_temporal_sm": "", # which date?
        "solr_geom": envelope,
        "solr_year_i": mod[0:4], # Modified year used
        "dct_references_s": references
    }
    # save GBL record to LTSB data directory
    outTitle = x["title"].replace(' ', '_')
    outTitle = outTitle.replace('*', '')
    with open('C:\\PROJECTS\\Directed_Studies\\esriscanner\\data-ltsb\\' + outTitle + ".json", 'w') as k:
        json.dump(temp_obj, k, indent=1)

# call update script to injest LTSB GBL records
os.system("py update.py -aj C:\\PROJECTS\\Directed_Studies\\esriscanner\\data-ltsb\\ -i test")

# Create GBL records from DNR data
# open and read data.json
dnrRead = urllib.request.urlopen("http://data-wi-dnr.opendata.arcgis.com/data.json").read()
dnrJson = json.loads(dnrRead.decode('utf-8'))
with open('C:\\PROJECTS\\Directed_Studies\\esriscanner\\dnrTest.json', 'w') as dnrCont:
    json.dump(dnrJson, dnrCont, indent=1)
# loop through each record
for record in dnrJson["dataset"]:
    # call html strip function
    description = strip_tags(record["description"])
    access = record["accessLevel"].capitalize()
    envelope = "ENVELOPE(" + record["spatial"] + ")"
    identifier = record["identifier"]
    # create slug from end of identifier and 'WI_DNR_'
    slug = "WI_DNR_" + record["identifier"].replace('http://data-wi-dnr.opendata.arcgis.com/datasets/','')
    mod = record["modified"]
    geomType = ""
    # grab raw metadata if available and get geom type
    if("FeatureServer" in record["webService"] or "MapServer" in record["webService"]):
        meta = urllib.request.urlopen(record["webService"] + "?f=pjson").read()
        metajson = json.loads(meta.decode('utf-8'))
        if ("geometryType" in metajson):
            geomType = metajson["geometryType"].replace('esriGeometry', '')
    else:
        geomType = ""
    # create references from distribution, webService, and identifier
    references = "{"
    for dis in record["distribution"]:
        if 'downloadURL' in dis:
            references += '\"http://schema.org/downloadUrl\":\"' + dis["downloadURL"] + '\",'
    if ('https://p.widencdn.net/' in record["webService"]):
        references += '\"http://schema.org/downloadUrl\":\"' + record["webService"] + '\",'
    if (record["webService"].endswith('.zip')):
        references += '\"http://schema.org/downloadUrl\":\"' + record["webService"] + '\",'
    references += '\"http://schema.org/url\":\"' + record["identifier"] + '\",'
    references += "}"
    references = references.replace(",}", "}")
    # format gbl record
    dnr_temp_obj = {
        "geoblacklight_version": "1.0",
        "dc_identifier_s": identifier,
        "dc_title_s": record["title"],
        "dc_description_s": description,
        "dc_rights_s": access,
        "dct_provenance_s": record["publisher"]["name"],
        "layer_id_s": "", # leave blank? 
        "layer_slug_s": slug,
        "layer_geom_type_s": geomType, # type not in data.json
        "layer_modified_dt": record["modified"],
        "dc_format_s": "Shapefile", # all esri sites so probably shapefile?
        "dc_language_s": "English",
        "dct_isPartOf_sm": "Wisconsin Legislative Technology Services Bureau Open Data",
        "dc_creator_sm": record["publisher"]["name"],
        "dc_type_s": "Dataset",
        "dc_subject_sm": record["keyword"],
        "dct_spatial_sm": "", # no spatial field in data.json
        "dct_issued_s": record["issued"],
        "dct_temporal_sm": "", # which date?
        "solr_geom": envelope,
        "solr_year_i": mod[0:4], # Modified year used
        "dct_references_s": references
    }
    # save GBL record to LTSB data directory
    outTitle = record["title"].replace(' ', '_')
    outTitle = outTitle.replace('*', '')
    outTitle = outTitle.replace('/', '')
    with open('C:\\PROJECTS\\Directed_Studies\\esriscanner\\data-wi-dnr\\' + outTitle + ".json", 'w') as k:
        json.dump(dnr_temp_obj, k, indent=1)

# call update script to injest DNR GBL records
os.system("py update.py -aj C:\\PROJECTS\\Directed_Studies\\esriscanner\\data-wi-dnr\\ -i test")
