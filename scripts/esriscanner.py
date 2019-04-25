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

# Non standard python libraries
# requires additional installation
# ruamel.yaml: python -m pip install ruamel.yaml
import ruamel.yaml as yaml


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

def json2gbl (jsonUrl, collection, siteName, partOf):
    if (os.path.isdir('C:/PROJECTS/Directed_Studies/esriscanner/' + collection) == True):
        shutil.rmtree('C:/PROJECTS/Directed_Studies/esriscanner/' + collection)
    os.makedirs('C:/PROJECTS/Directed_Studies/esriscanner/' + collection)
    s = urllib.request.urlopen(jsonUrl).read()
    d = json.loads(s.decode('utf-8'))
    for x in d["dataset"]:
        # call html strip function
        description = strip_tags(x["description"])
        if (collection == "LTSB_OpenData"):
            description = description.replace('Attribute Field Definitions', '')
        access = x["accessLevel"].capitalize()
        innerEnv = [l for l in x["spatial"].split(',')]
        envelope = "ENVELOPE(" + innerEnv[0] + ", " +  innerEnv[2] + ", " + innerEnv[3] + ", " + innerEnv[1] + ")"
        identifier = x["identifier"]
        # create slug from end of identifier and 'LTSB_OpenData_'
        slug = collection.replace("OpenData", "") + "_" + x["identifier"].replace('http://' + siteName + '.opendata.arcgis.com/datasets/','')
        mod = x["modified"]
        geomType = ""
        # grab raw metadata if available and get geom type
        if("FeatureServer" in x["webService"] or "MapServer" in x["webService"]):
            a = urllib.request.urlopen(x["webService"] + "?f=pjson").read()
            b = json.loads(a.decode('utf-8'))
            if("geometryType" in b):
                geomType = b["geometryType"].replace('esriGeometry', '')
        # create references from distribution 
        references = "{"
        for t in x["distribution"]:
            if 'downloadURL' in t:
                references += '\"http://schema.org/downloadUrl\":\"' + t["downloadURL"] + '\",'
        if ('https://p.widencdn.net/' in x["webService"]):
            references += '\"http://schema.org/downloadUrl\":\"' + x["webService"] + '\",'
        if (x["webService"].endswith('.zip')):
            references += '\"http://schema.org/downloadUrl\":\"' + x["webService"] + '\",'
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
            "layer_id_s": "", 
            "layer_slug_s": slug,
            "layer_geom_type_s": geomType, 
            "layer_modified_dt": x["modified"],
            "dc_format_s": "File", 
            "dc_language_s": "English",
            "dct_isPartOf_sm": partOf,
            "dc_creator_sm": x["publisher"]["name"],
            "dc_type_s": "Dataset",
            "dc_subject_sm": x["keyword"],
            "dct_spatial_sm": "", # no spatial field in data.json
            "dct_issued_s": x["issued"],
            "dct_temporal_sm": "", 
            "solr_geom": envelope,
            "solr_year_i": mod[0:4], 
            "dct_references_s": references
        }
        # Check if required elements have valid data before calling update.py
        scanCatch = "\n"
        if(temp_obj["dc_identifier_s"] == ""):
            scanCatch += "dc_identifier_s\n"
        if(temp_obj["layer_slug_s"] == ""):
            scanCatch += "layer_slug_s\n"
        if(temp_obj["dc_title_s"] == ""):
            scanCatch += "dc_title_s\n"
        if("NaN" in temp_obj["solr_geom"] ):
            scanCatch += "solr_geom\n"
        if(temp_obj["dct_provenance_s"] == ""):
            scanCatch += "layer_slug_s\n"
        if(temp_obj["dc_rights_s"] == ""):
            scanCatch += "layer_slug_s\n"
        if(temp_obj["geoblacklight_version"] == ""):
            scanCatch += "geoblacklight_version\n"
        if(temp_obj["solr_year_i"] == 9999):
            scanCatch += "solr_year_i\n"
        # save GBL record to collection data directory
        outTitle = x["title"].replace(' ', '_')
        outTitle = outTitle.replace('*', '')
        outTitle = outTitle.replace('/', '')
        if (scanCatch == "\n"):
            with open('C:\\PROJECTS\\Directed_Studies\\esriscanner\\' + collection + "\\" + outTitle + ".json", 'w') as k:
                json.dump(temp_obj, k, indent=1)
    os.system("python update.py -aj C:\\PROJECTS\\Directed_Studies\\esriscanner\\" + collection + "\\ -i prod")

# loop through each collection in OpenData.yml and call json2gbl function
with open("C:\\PROJECTS\\Directed_Studies\\esriscanner\\OpenData.yml") as stream:
    theDict = yaml.safe_load(stream)
    for record in theDict["Sites"]:
        siteRecord = theDict["Sites"][record]
        json2gbl(siteRecord["SiteURL"], record , siteRecord["SiteShort"], siteRecord["CollectionName"])
