"""
esriscanner.py

Author(s): Ben Segal

Description: 
This script is designed to run each day and scan Esri open data sites for data.  No attempt is made to track new/removed datasets.  Instead, our model is to start fresh with a new set of records each day. The process begins by first wiping out any existing records for each site in solr, then re-ingesting whatever is found during the scan.  This guarantees, as much as we can, that links to these scanned datasets are accurate and up-to-date.

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

"""
To-do:
 - specify output location for scanner files
 - add ability to specify target instance when called (dev, prod, test)
 - what happens if an individual "scan" fails? (currently entire script will fail without graceful exit; would prefer any "good" scans to complete with a notice sent to operator about failed scans.)
 - is there a reason to keep json files after ingest completes?  make it optional?
 - re-engineer: 
     - focus on "provenance" to organize records instead of "collections"
     - understand why LTSB options are hard-coded
     - This script will eventually live on a unix server.  Calling update.bat needs to be modified.  Call update.py directly?  (may be preferable to replicate key ingest code in this script instead?)
     - No need to save json files that contain all records for each site; ingest is based on records contained in subdirectories.
"""

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

def json2gbl (jsonUrl, collection, createdBy, siteName, partOf, prefix, postfix):
    if (os.path.isdir(collection) == True):
        shutil.rmtree( collection)
    os.makedirs(collection)
    s = urllib.request.urlopen(jsonUrl).read()
    d = json.loads(s.decode('utf-8'))
    with open(collection + '.json', 'w') as fout:
        json.dump(d, fout, indent=1)
    for x in d["dataset"]:
        # call html strip function
        description = strip_tags(x["description"])
        ##### red flag: specific use-case hardcoded #####
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
        # "dct_provenance_s": x["publisher"]["name"],
        #"dc_subject_sm": x["keyword"],
        temp_obj = {
            "geoblacklight_version": "1.0",
            "dc_identifier_s": identifier,
            "dc_title_s": prefix + x["title"] + ", " + createdBy,
            "dc_description_s": description,
            "dc_rights_s": access,
            "dct_provenance_s": createdBy,
            "layer_id_s": "", 
            "layer_slug_s": slug,
            "layer_geom_type_s": "", 
            "layer_modified_dt": x["modified"],
            "dc_format_s": "File", 
            "dc_language_s": "English",
            "dct_isPartOf_sm": partOf,
            "dc_creator_sm": createdBy,
            "dc_type_s": "Dataset",
            "dc_subject_sm": "",
            "dct_spatial_sm": "", 
            "dct_issued_s": x["issued"],
            "dct_temporal_sm": "", 
            "solr_geom": envelope,
            "solr_year_i": mod[0:4], 
            "dct_references_s": references,
            "uw_supplemental_s" : "",
            "uw_notice_s": "This dataset was automatically cataloged from the author/publisher's Open Data Portal. In some cases, publication dates and bounding coordinates may be incorrect.  Please check the 'More details link' for additional information.",
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
            with open(collection + "\\" + outTitle + ".json", 'w') as k:
                json.dump(temp_obj, k, indent=1)
    # rather than calling update.bat/.py, which is designed to accomplish more than adding new json recs to solr,
    # maybe we should handle all solr ingests in the "scanner" here instead???  The QA check above is redundant
    # with update.py.  The QA check was replicated here, because if it failed during update.bat, there is no way for the scanner script to know update.py failed.  Similarly, there could be other reasons update.py can fail... and if it does, scanner.py will likely not fail gracefully.
    os.system("r:\\scripts\\update.bat -a " +  collection + "\\ -i dev")

# loop through each collection in OpenData.yml and call json2gbl function
with open("OpenData.yml") as stream:
    theDict = yaml.safe_load(stream)
    for record in theDict["Sites"]:
        siteRecord = theDict["Sites"][record]
        json2gbl(siteRecord["SiteURL"], record , siteRecord["CreatedBy"], siteRecord["SiteShort"], siteRecord["CollectionName"],siteRecord["DatasetPrefix"],siteRecord["DatasetPostfix"])
