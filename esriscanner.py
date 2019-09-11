"""
esriscanner.py

Authors: Ben Segal, Jim Lacy, Eli Wilz

Description: 
This script is designed to run each day and scan Esri open data sites for data.  No attempt is made to track new/removed datasets.  Instead, our model is to start fresh with a new set of records each day. The process begins by first wiping out any existing records for each site in solr, then re-ingesting whatever is found during the scan.  This guarantees, as much as we can, that links to these scanned datasets are accurate and up-to-date.

Dependencies: Python 3.x
"""
import json
import urllib.request
from html.parser import HTMLParser
import shutil
import os
import re

# Non standard python libraries
# requires additional installation
# python -m pip install ruamel.yaml
import ruamel.yaml as yaml

"""
To-do:

 - examine geographic envelope of each record
      - if bounding box is off the coast of west africa, ignore record
      - if bounding box has a smaller extent than Wisconsin, override collection name... should *not* be labeled Statewide (example:  DNR records for Rock River)
 - see if we can cook up a method to exclude docs, apps
 - scan keywords field for iso categories
    
"""

# Strip html from description
# need better description of what this does
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
    # Check to see if critical keys are found.  If not, check fails with False
    validData = True
    msg=""
    if 'description' not in dataset: 
        msg += "          No description found."
        validData = False
    if 'identifier' not in dataset: 
        msg += "          No identifier found."
        validData = False  
    if 'modified' not in dataset: 
        msg += "          No modified date found."
        validData = False   
    if 'spatial' not in dataset: 
        msg += "          No bounding box found."
        validData = False
    return validData,msg

def getURL(refs):
    # For uknown reasons, ARGIS Hub is inconsistent in outputting the type of url.
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
    

def json2gbl (jsonUrl, createdBy, siteName, collectionName, prefix, postfix):
    
    # subfolders for scanned sites will be dumped here
    basedir = "d:\projects\geodata\geodata-processing\scanner"
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
    
    # loop through each dataset in the json file
    # note: Esri's dcat records call everything a "dataset"
    for dataset in d["dataset"]:                       
        validData,msg = checkValidity(dataset)
        if validData:           
            # call html strip function
            description = strip_tags(dataset["description"])
                 
            # read access level... should always be public
            access = dataset["accessLevel"].capitalize()
            
            # generate bounding box
            coordinates = [l for l in dataset["spatial"].split(',')]
            envelope = "ENVELOPE(" + coordinates[0] + ", " +  coordinates[2] + ", " + coordinates[3] + ", " + coordinates[1] + ")"
            
            # read DCAT dataset identifier
            # Hub typically outputs a full url with UUID for the identifier.  We just want the uuid.
            identifier = dataset["identifier"].split('/')[-1]
            #print(identifier)

            
            # create slug from end of identifier
            # needs more work, not sure how reliable this method is
            # parse on /, and take rightmost element
            slug = siteName + "_" + identifier
            
            # Although not ideal, we use "modified" field for our date
            # ArcGIS Hub's handling of dates is sketchy at best
            modifiedDate = dataset["modified"]
            
            # DCAT records from Hub make no references to the type of geometry!!
            geomType = ""
            
            # create references from distribution        
            references = "{"
            for refs in dataset["distribution"]:
                url=getURL(refs)
                #print(url)

                if (refs["format"] == "Web Page" and url != "invalid"):
                    references += '\"http://schema.org/url\":\"' + url + '\",'
                #elif (refs["format"] == "Esri REST" and url != "invalid"):
                #        references += '\"urn:x-esri:serviceType:ArcGIS#FeatureLayer\":\"'  + url +  '\",'
                #elif (refs["format"] == "GeoJSON" and url != "invalid"):
                #    references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'
                #elif (refs["format"] == "CSV" and url != "invalid"):
                #    references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'
                #elif (refs["format"] == "KML" and url != "invalid"):
                #    references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'
                elif (refs["format"] == "ZIP" and url != "invalid"):
                    references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'     
            references += "}"
            references = references.replace(",}", "}")
                  
            # format gbl record
            gbl = {
                "geoblacklight_version": "1.0",
                "dc_identifier_s": slug,
                "dc_title_s": prefix + dataset["title"] + postfix,
                "dc_description_s": description,
                "dc_rights_s": access,
                "dct_provenance_s": createdBy,
                "layer_id_s": "", 
                "layer_slug_s": slug,
                "layer_geom_type_s": "", 
                "layer_modified_dt": "",
                "dc_format_s": "File", 
                "dc_language_s": "English",
                "dct_isPartOf_sm": collectionName,
                "dc_creator_sm": createdBy,
                "dc_type_s": "Dataset",
                "dc_subject_sm": "",
                "dct_spatial_sm": "", 
                "dct_issued_s": "", 
                "dct_temporal_sm": "", 
                "solr_geom": envelope,
                "solr_year_i": modifiedDate[0:4], 
                "dct_references_s": references,
                "uw_supplemental_s" : "",
                "uw_notice_s": "This dataset was automatically cataloged from the author's Open Data Portal. In some cases, publication year and bounding coordinates shown here may be incorrect.  Please check the 'More details at' link for additional information.",
            }
          
            # Strip special characters from title for json filename      
            outFileName=re.sub('[^A-Za-z0-9]+', '',dataset["title"])
            #print(outFileName)
            
            # dump the generated GBL record to a file
            with open(path + "\\" + outFileName + ".json", 'w') as jsonfile:
                json.dump(gbl, jsonfile, indent=1)
        else:
            print("     Validity check failed on " + prefix + dataset["title"] + postfix)
            print(msg)
   
   
# loop through each site in OpenData.yml and call json2gbl function
with open("OpenData.yml") as stream:
    theDict = yaml.safe_load(stream)
    for siteCode in theDict["Sites"]:
        site = theDict["Sites"][siteCode]
        print("\n\nProcessing Site: " + siteCode)
        json2gbl(site["SiteURL"], site["CreatedBy"], site["SiteName"], site["CollectionName"],site["DatasetPrefix"],site["DatasetPostfix"])
