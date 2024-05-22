"""
esriscanner.py

Ben Segal and Jim Lacy
Wisconsin State Cartographer's Office
GeoData@Wisconsin

Description:
This script is designed to run periodically and scan Esri open data sites for metadata, and output a series of GeoBlacklight metadata files for all items found.  No attempt is made to track new/removed datasets.  Instead, our model is to start fresh with a new set of records each run. This guarantees, as much as we can, that links to these scanned datasets are accurate and up-to-date.  We have a separate process to ingest GBL metadata records produced by this script.

Dependencies: Python 3.x

To-do:

 - examine geographic envelope of each record
      - if bounding box has a smaller extent than Wisconsin, override collection name... should *not* be labeled Statewide (example:  DNR records for Rock River)

"""
import json
import shutil
import os
import re

from argparse import ArgumentParser, FileType
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs


# External python libraries follow
# requires additional installation
# python -m pip install -r requirements.txt
import requests
from requests.exceptions import *

from ruamel.yaml import YAML
yaml = YAML()

import tenacity as t # we need a lot of properties from tenacity so using short name



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

# minX/West, minY/South, maxX/east, maxY/North
spatial_coords = re.compile(r'(?P<minX>[^,]+),(?P<minY>[^,]+),(?P<maxX>[^,]+),(?P<maxY>[^,]+)')
def checkValidity(dataset):
    # Check to see if critical keys are missing data.  If not, check fails with False
    validData = True
    errors = []

    if 'identifier' not in dataset or not dataset["identifier"]:
        errors.append("No identifier found.")
        validData = False
    if 'modified' not in dataset or not dataset["modified"]:
        errors.append("No modified date found.")
        validData = False
    # Known "bad" values include "{{extent}} and {{extent:computeSpatialProperty}}"
    if not spatial_coords.match(dataset.get("spatial", "")):
        errors.append(f"No spatial bounding box found{('spatial' in dataset and ' in ' + dataset['spatial']) or None}.")
        validData = False
    return validData,"\t".join(errors)

def getURL(refs):
    # For unknown reasons, ARGIS Hub is inconsistent in outputting the type of url.
    # Sometimes references use the key of "accessURL," other times "downloadURL"
    # This function checks to see which is present, and returns appropriate url
    # in addition, distribution methods may be defined, but the URL is missing.  For example:
    """{
                    "@type": "dcat:Distribution",
                    "title": "Esri Rest API",
                    "format": "Esri REST",
                    "mediaType": "application/json"
        }"""
    if ('accessURL') in refs:
        url=refs["accessURL"]
    elif ('downloadURL') in refs:
        url=refs["downloadURL"]
        print(url)
    else:
        #error, no url found
        url="invalid"
    return url

def get_iso_topic_categories(keywords):
    # parse the provided keyword list and extract/standardize all found ISO keywords

    iso_categories_list = []
    iso_crosswalk = {'biota':'Biota',
                 'boundaries':'Boundaries',
                 'climatologyMeteorologyAtmosphere':'Atmospheric Sciences',
                 'atmospheric sciences':'Atmospheric Sciences',
                 'economy':'Economy',
                 'elevation':'Elevation',
                 'environment':'Environment',
                 'farming':'Farming',
                 'geoscientificInformation':'Geoscientific Information',
                 'geoscientific':'Geoscientific Information',
                 'geoscientific information':'Geoscientific Information',
                 'health':'Health',
                 'imagery and base maps':'Imagery and Base Maps',
                 'imagerybasemapsearthcover':'Imagery and Base Maps',
                 'imagery & basemaps':'Imagery and Base Maps',
                 'imagery & base maps':'Imagery and Base Maps',
                 'imagery and base maps':'Imagery and Base Maps',
                 'inland waters':'Inland Waters',
                 'inlandwaters':'Inland Waters',
                 'intelligence and military':'Intelligence and Military',
                 'military and intelligence':'Intelligence and Military',
                 'intelligence & military':'Intelligence and Military',
                 'military & intelligence':'Intelligence and Military',
                 'intelligencemilitary':'Intelligence and Military',
                 'location':'Location',
                 'oceans':'Oceans',
                 'planningCadastre':'Planning and Cadastral',
                 'planning and cadastre':'Planning and Cadastral',
                 'planning & cadastre':'Planning and Cadastral',
                 'planning and cadastral':'Planning and Cadastral',
                 'planning & cadastral':'Planning and Cadastral',
                 'society':'Society',
                 'structure':'Structure',
                 'transportation':'Transportation',
                 'utilitiesCommunication':'Utilities and Communication',
                 'utilities and communication':'Utilities and Communication',
                 'utilities & communication':'Utilities and Communication'
                 }

    for keyword in keywords:
        keyvalue = iso_crosswalk.get(keyword.lower())
        if keyvalue:
            iso_categories_list.append(keyvalue)
    return iso_categories_list


def add_dataset_collections(keywords):
    # parse the provided keyword list and map found keywords to specific GeoData collections

    collection_list = []
    # format is keyword:collection
    collection_crosswalk = {'climate':'Climate',
                             'climate change':'Climate',
                             'Environmental justice':'Climate',
                             'environmental justice':'Climate',
                             'groundwater':'Geology and Groundwater',
                             'geology':'Geology and Groundwater',
                             'watershed':'Geology and Groundwater',
                             'water table':'Geology and Groundwater',
                             'GCSM':'Geology and Groundwater',
                             'surficial deposits':'Geology and Groundwater'}

    for keyword in keywords:
        keyvalue = collection_crosswalk.get(keyword.lower())
        if keyvalue:
            collection_list.append(keyvalue)
            #print("Key value is " + str(keyvalue))
            #print("appended to list")
    #print(collection_list)
    return collection_list


def json2gbl (d, createdBy, siteName, collections, prefix, postfix, skiplist, basedir):
    now = datetime.now(timezone.utc) # used to populate layer_modified_dt, which must be in UTC

    path = os.path.join(basedir,siteName)

    # if site folder already exists, delete
    # we start fresh each run
    if (os.path.isdir(path) == True):
        shutil.rmtree(path)

    # create folder to hold json output files
    os.makedirs(path)

    # Parse through the collections defined for each site
    site_collections = []
    for CollectionName in collections:
        site_collections.append(CollectionName["CollectionName"])
    #print(site_collections)

    # Parse through the skiplist defined for each site
    uuidList = []
    for uuidnum in skiplist:
        uuidList.append(uuidnum["UUID"])

    # loop through each dataset in the json file
    # note: Esri's dcat records call everything a "dataset"
    for dataset in d["dataset"]:
        #print(dataset)
        # read DCAT dataset identifier
        # Esri keeps messing with the formatting of this field!
        #
        # Also, it appears that at times the "unique" ID found in the querystring is replicated across multiple
        # datasets. My hack is to append the "sublayer" number to the identifier.  Without taking this action,
        # there will be situations where records will be overwritten since we name json files based on the
        # identifier.
        querystring = parse_qs(urlparse(dataset["identifier"]).query)
        if len(querystring) > 1:
            #print(querystring)
            identifier = siteName + "-" + querystring["id"][0] + querystring["sublayer"][0]
        else:
            identifier = siteName + "-" + querystring["id"][0]
        #print(identifier)
        #print(dataset["title"])
        dataset_collections = []
        collections = []
        validData,msg = checkValidity(dataset)
        if validData and (identifier not in uuidList):
            # call html strip function
            description = strip_tags(dataset["description"])

            # check for empty description that sometimes shows up in Hub sites
            if description == '{{default.description}}' or description == '' or description == '{{description}}':
                description = 'No description provided.'

            # read access level... should always be Public
            access = dataset["accessLevel"].capitalize()

            # generate bounding box
            coordinates = dataset["spatial"].split(',')
            #print(coordinates)
            envelope = "ENVELOPE(" + coordinates[0] + ", " +  coordinates[2] + ", " + coordinates[3] + ", " + coordinates[1] + ")"

            # send the dataset keywords to a function that parses and returns a standardized list
            # of ISO Topic Keywords
            iso_categories_list = get_iso_topic_categories(dataset["keyword"])

            # send the dataset keywords to a function that parses and returns a standardized standardized collection names
            dataset_collections = add_dataset_collections(dataset["keyword"])
            if dataset_collections:
                collections = dataset_collections + site_collections
            else:
                collections = site_collections

            # Although not ideal, we use "modified" field for our date
            # ArcGIS Hub's handling of dates is sketchy at best
            modifiedDate = dataset["modified"]

            # Esri DCAT records from Hub make no references to the type of geometry!!
            # For now, we default all of these records to Mixed... no better option
            geomType = "Mixed"

            # create references from distribution
            #print(">>>>>>>>>> " + dataset["title"])
            references = "{"
            references += '\"http://schema.org/url\":\"' + dataset["landingPage"] + '\",'
            for refs in dataset["distribution"]:
                url=getURL(refs)

                #Fix the encoding of goofy querystring now intrinsic to Esri download links
                url = url.replace("\"","%22").replace(",","%2C").replace("{","%7B").replace("}","%7D")
                #print(url)

                # In July 2021, we started seeing distribution formats with null values
                if refs["format"] is not None:
                    if (refs["format"] == "ArcGIS GeoServices REST API" and url != "invalid"):
                            if ('FeatureServer') in url:
                                references += '\"urn:x-esri:serviceType:ArcGIS#FeatureLayer\":\"'  + url +  '\",'
                                #print("Found featureServer")
                            elif ('ImageServer') in url:
                                references += '\"urn:x-esri:serviceType:ArcGIS#ImageMapLayer\":\"'  + url +  '\",'
                                #print("Found ImageServer")
                            elif ('MapServer') in url:
                                references += '\"urn:x-esri:serviceType:ArcGIS#DynamicMapLayer\":\"'  + url +  '\",'
                                #print("Found MapServer Layer")
                    elif (refs["format"] == "ZIP" and url != "invalid"):
                        references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'
            references += "}"
            references = references.replace(",}", "}")
            dc_creator_sm = []
            dc_creator_sm.append(createdBy)
            dct_temporal_sm = []
            dct_temporal_sm.append(modifiedDate[0:4])
            #print("\n")
            # format gbl record
            #print(dataset["title"])
            gbl = {
                "geoblacklight_version": "1.0",
                "dc_identifier_s": identifier,
                "dc_title_s": prefix + str(dataset["title"]) + postfix,
                "dc_description_s": description,
                "dc_subject_sm": iso_categories_list,
                "dc_rights_s": access,
                "dct_provenance_s": createdBy,
                "layer_id_s": "",
                "layer_slug_s": identifier,
                "layer_geom_type_s": geomType,
                "dc_format_s": "File",
                "dc_language_s": "English",
                "dct_isPartOf_sm": collections,
                "dc_creator_sm": dc_creator_sm,
                "dc_type_s": "Dataset",
                "dct_spatial_sm": "",
                "dct_issued_s": "",
                "dct_temporal_sm": dct_temporal_sm,
                "solr_geom": envelope,
                "solr_year_i": int(modifiedDate[0:4]),
                "layer_modified_dt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dct_references_s": references,
                "uw_notice_s": "This dataset was automatically cataloged from the author's Open Data Portal. In some cases, publication year and bounding coordinates shown here may be incorrect. Additional download formats may be available on the author's website. Please check the 'More details at' link for additional information.",
            }

            outFileName = identifier

            # dump the generated GBL record to a file
            with open(path + "\\" + outFileName + ".json", 'w') as jsonfile:
                json.dump(gbl, jsonfile, indent=1)
        elif not validData:
            print("********** Validity check failed on " + prefix + dataset["title"] + postfix)
            print(msg)
        else:
            print("---------- Skipping dataset: " + prefix + dataset["title"] + postfix)

@t.retry(retry=t.retry_if_exception_type((Timeout,HTTPError,),),
         wait=t.wait_exponential_jitter(initial=3.0, max=10.0, jitter=1.0),
         stop=t.stop_after_attempt(5),
         after=lambda x,y: print((x, y,)))
def getSiteJSON(siteURL, session):
    try:
        resp = session.get(siteURL, timeout=30)
    except SSLError:
        resp = session.get(siteURL, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.json()

def main():
    '''Main body of script'''
    ap = ArgumentParser(description='''Scans ESRI hubs for distributions''')
    ap.add_argument('--config-file', default=r"C:\Users\lacy.ad\Documents\scripts\OpenData.yml")
    args = ap.parse_args()
    session = requests.Session()
    # YAML configuration file
    with open(args.config_file) as stream:
        theDict = yaml.load(stream)
    # Subfolders for scanned sites will be dumped here
    output_basedir = theDict.get('output_basedir', r"C:\Users\lacy.ad\Documents\scripts\opendata")

    # loop through each site in OpenData.yml and call json2gbl function
    for siteCode in theDict["Sites"]:
        site = theDict["Sites"][siteCode]
        print("\n\nProcessing Site: " + siteCode)
        #print(site["Collections"])
        #print(site["DatasetPrefix"])
        #print(site["DatasetPostfix"])
        site_data = None
        try:
            site_data = getSiteJSON(site['SiteURL'], session)
        except Exception as e:
            print(e)
            print("**** Site Failure, check URL for " + site["CreatedBy"] + "****")
            continue
        print(site["SiteURL"])
        json2gbl(site_data, site["CreatedBy"], site["SiteName"], site["Collections"],site["DatasetPrefix"],site["DatasetPostfix"],site["SkipList"],output_basedir)

if __name__ == '__main__':
    main()
