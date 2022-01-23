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
import urllib.request
from html.parser import HTMLParser
import shutil
import os
import re
import ssl
from datetime import datetime
from datetime import timezone

# Non-standard python libraries follow
# requires additional installation
# python -m pip install ruamel.yaml
import ruamel.yaml as yaml

# Subfolders for scanned sites will be dumped here
output_basedir = "C:\\Users\\lacy\\Documents\\scripts\\opendata"

# YAML configuration file
config_file = "C:\\Users\\lacy\\Documents\\scripts\\OpenData.yml"

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

def checkValidity(dataset):
    # Check to see if critical keys are missing data.  If not, check fails with False
    validData = True
    msg=""
    if 'identifier' not in dataset or dataset["identifier"] == "": 
        msg += "           No identifier found."
        validData = False  
    if 'modified' not in dataset or dataset["modified"] == "": 
        msg += "           No modified date found."
        validData = False   
    if 'spatial' not in dataset or dataset["spatial"] == "{{extent}}" or dataset["spatial"] == "": 
        msg += "           No spatial bounding box found."
        validData = False        
    return validData,msg

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
  

def json2gbl (jsonUrl, createdBy, siteName, collections, prefix, postfix, skiplist, basedir):
    
    
    now = datetime.now(timezone.utc) # used to populate layer_modified_dt, which must be in UTC
    
    path = os.path.join(basedir,siteName)
    
    # if site folder already exists, delete
    # we start fresh each run
    if (os.path.isdir(path) == True):
        shutil.rmtree(path)
    
    # create folder to hold json output files
    os.makedirs(path)
    
    # grab json data from url
    s = urllib.request.urlopen(jsonUrl).read()
   
    # decode data grabbed from url
    d = json.loads(s.decode('utf-8'))
    
    # Parse through the collections defined for each site           
    collectionList = []
    for CollectionName in collections:
        collectionList.append(CollectionName["CollectionName"])
    #print(collectionList)
    
    # Parse through the skiplist defined for each site           
    uuidList = []
    for uuidnum in skiplist:
        uuidList.append(uuidnum["UUID"])
    
    # loop through each dataset in the json file
    # note: Esri's dcat records call everything a "dataset"
    for dataset in d["dataset"]:  
        
        # read DCAT dataset identifier
        # Hub outputs a full url for the identifier.  We just want the dataset name.
        identifier = dataset["identifier"].split('/')[-1]
             
        # get rid of the extra garbage esri includes in url as of January 2022
        identifier = identifier.replace("::","-")
        #print(identifier)
        
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
            coordinates = [l for l in dataset["spatial"].split(',')]
            envelope = "ENVELOPE(" + coordinates[0] + ", " +  coordinates[2] + ", " + coordinates[3] + ", " + coordinates[1] + ")"
            
            # send the dataset keywords to a function that parses and returns a standardized list
            # of ISO Topic Keywords
            iso_categories_list = get_iso_topic_categories(dataset["keyword"])        
            
            # Although not ideal, we use "modified" field for our date
            # ArcGIS Hub's handling of dates is sketchy at best
            modifiedDate = dataset["modified"]
            
            # Esri DCAT records from Hub make no references to the type of geometry!!
            # For now, we default all of these records to Mixed... no better option 
            geomType = "Mixed"
            
            # create references from distribution        
            print(">>>>>>>>>> " + dataset["title"])
            references = "{"
            for refs in dataset["distribution"]:
                url=getURL(refs)
                
                #Fix the encoding of goofy querystring now intrinsic to Esri download links
                url = url.replace("\"","%22").replace(",","%2C").replace("{","%7B").replace("}","%7D")
                #print(url)
                
                # In July 2021, we started seeing distribution formats with null values
                if refs["format"] is not None:
                    # Seriously, Esri sometimes outputs "Web page" or "Web Page" for the page reference.  Ugh!
                    if (refs["format"].lower() == "web page" and url != "invalid"):
                        references += '\"http://schema.org/url\":\"' + url + '\",'
                    elif (refs["format"] == "ArcGIS GeoServices REST API" and url != "invalid"):
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
            gbl = {
                "geoblacklight_version": "1.0",
                "dc_identifier_s": identifier,
                "dc_title_s": prefix + dataset["title"] + postfix,
                "dc_description_s": description,
                "dc_subject_sm": iso_categories_list,
                "dc_rights_s": access,
                "dct_provenance_s": createdBy,
                "layer_id_s": "", 
                "layer_slug_s": identifier,
                "layer_geom_type_s": geomType, 
                "dc_format_s": "File", 
                "dc_language_s": "English",
                "dct_isPartOf_sm": collectionList,
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
   
def validSite (siteURL):
    req = urllib.request.Request(siteURL)
    # for unknown reasons, some sites fail with a SSL "unable to verify" error. The errors would also reference an expired certificate, which wasn't true! The following line is a hack that skips verification.
    ssl._create_default_https_context = ssl._create_unverified_context
    try: urllib.request.urlopen(req)
    except urllib.error.URLError as e:
        print(e.reason)
        return False
    else:
        return True

   
# loop through each site in OpenData.yml and call json2gbl function
with open(config_file) as stream:
    theDict = yaml.safe_load(stream)
    for siteCode in theDict["Sites"]:
        site = theDict["Sites"][siteCode]
        print("\n\nProcessing Site: " + siteCode)
        #print(site["Collections"])
        if validSite(site["SiteURL"]):
            json2gbl(site["SiteURL"], site["CreatedBy"], site["SiteName"], site["Collections"],site["DatasetPrefix"],site["DatasetPostfix"],site["SkipList"],output_basedir)
            #os.system("pause")
        else:
            print("**** Site Failure, check URL for " + site["CreatedBy"] + "****")
        
