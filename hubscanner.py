"""
hubscanner.py

Jim Lacy and Ben Segal
Wisconsin State Cartographer's Office
GeoData@Wisconsin

Special thanks to Dave Mayo from Harvard University for contributing a number of important logging, notification, and other quality improvements!

Description:
This script is designed to run periodically and scan Esri open data sites for metadata, and output a series of GeoBlacklight metadata files for all items found.  No attempt is made to track new/removed datasets. 
 Instead, our model is to start fresh with a new set of records each run. This guarantees, as much as we can, that links to these scanned datasets are accurate and up-to-date.  

"""
import json
import logging
import os
import shutil
import smtplib
import sys
import pysolr
import glob
from argparse import ArgumentParser
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import StringIO
from urllib.parse import urlparse, parse_qs
from requests.auth import HTTPBasicAuth
import requests
from requests.exceptions import *
from ruamel.yaml import YAML
yaml = YAML()
import tenacity as t # we need a lot of properties from tenacity so using short name

# Make sure you have the right libraries installed with: 
# python -m pip install -r requirements.txt
# Note: reminder to use python3 when in Ubuntu/unix

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
    # Check to see if critical keys are missing, or are missing valid data.  If not, check fails with False.
    validData = True
    errors = []

    if 'identifier' not in dataset or not dataset["identifier"]:
        errors.append(f"          No valid identifier found")
        validData = False
    if 'title' not in dataset or not dataset["title"] or dataset["title"]=="{{name}}":
        errors.append(f"          No valid title found")
        validData = False
    if (not isinstance(dataset["spatial"], dict)):
        errors.append(f"          No valid valid spatial bounding box found in {dataset['spatial']}")
        validData = False
    return validData,"\n".join(errors)

def getURL(refs):
    global produce_report
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
        add_to_report(f"     Distribution missing all known distribution keys: keys actually present are: {list(refs.keys())}")
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

def validate_coordinates(coordinates,maxextent):
    fixed_coordinates = list(coordinates)
             
    # Coordinates are in the order: west, south, east, north
    # Check and fix western boundary  
    if coordinates[0] < maxextent[0]: 
        fixed_coordinates[0] = maxextent[0]
        log.debug(f"     Western boundary changed from {coordinates[0]} to {fixed_coordinates[0]}.")
    
    # Check and fix southern boundary
    # and make sure it is in northern hemisphere
    if coordinates[1] < maxextent[1] or coordinates[1] < 0:
        fixed_coordinates[1] = maxextent[1]
        log.debug(f"     Southern boundary changed from {coordinates[1]} to {fixed_coordinates[1]}.")    
        
    # Check and fix eastern boundary
    if coordinates[2] > maxextent[2]:
        fixed_coordinates[2] = maxextent[2]
        log.debug(f"     Eastern boundary changed from {coordinates[2]} to {fixed_coordinates[2]}.")
    
    # Check and fix northern boundary
    # and make sure it is in northern hemisphere
    if coordinates[3] > maxextent[3] or coordinates[1] < 0:
        fixed_coordinates[3] = maxextent[3]
        log.debug(f"     Northern boundary changed from {coordinates[3]} to {fixed_coordinates[3]}.")
    
    # We have seen situations where listed extent is only a point!
    # (Debateable whether this is correct or not)
    # or westernmost coordinate is larger than east
    # or northernmost coordinate is smaller than south
    if coordinates[0] == coordinates[2] or coordinates[1] == coordinates[3] or coordinates[0] > coordinates[2] or coordinates[1] > coordinates[3]:
        log.debug(f"     Suspect coordinates changed to MaxExtent")
        fixed_coordinates = maxextent
             
    return fixed_coordinates


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
            log.debug("Key value is " + str(keyvalue))
            log.debug("appended to list")
    log.debug(collection_list)
    return collection_list


def json2gbl (d, createdBy, siteName, collections, prefix, postfix, skiplist, maxextent, basedir):
    now = datetime.now(timezone.utc) # used to populate layer_modified_dt, which must be in UTC
    path = os.path.join(basedir,siteName)
    
    # create folder to hold json output files
    os.makedirs(path)

    # Parse through the collections defined for each site
    site_collections = []
    for CollectionName in collections:
        site_collections.append(CollectionName["CollectionName"])
    log.debug(site_collections)

    # Parse through the skiplist defined for each site
    uuidList = []
    for uuidnum in skiplist:
        uuidList.append(uuidnum["UUID"])

    # loop through each dataset in the json file
    # note: Esri's dcat records call everything a "dataset"
    for dataset in d["dataset"]:
        log.debug(dataset)                       
        dataset_collections = []
        collections = []
        validData,msg = checkValidity(dataset)
        
        if validData:
            querystring = parse_qs(urlparse(dataset["identifier"]).query)
            if len(querystring) > 1:
                identifier = siteName + "-" + querystring["id"][0] + querystring["sublayer"][0]
            else:
                identifier = siteName + "-" + querystring["id"][0]

            if identifier not in uuidList:
                log.debug(dataset["title"])

                # check for empty description that sometimes shows up in Hub sites
                if dataset["description"] == '{{default.description}}' or dataset["description"] == '' or dataset["description"] == '{{description}}':
                    description = 'No description provided.'
                else:
                    description = strip_tags(dataset["description"])
                
                # read access level... should always be Public
                access = dataset["accessLevel"].capitalize()

                # generate bounding box
                maxextents_list = [float(value) for value in maxextent]
                spatial = dataset["spatial"]
                log.debug(f"{spatial}")

                if spatial["type"]=="envelope":
                    log.debug(f"{spatial['type']}")
                    log.debug(f"{spatial['coordinates']}")
                    coordinates = [float(coord) for pair in spatial['coordinates'] for coord in pair]
                    log.debug(f"{coordinates}")       
                    valid_coordinates = validate_coordinates(coordinates, maxextents_list)            
                    envelope = f"ENVELOPE({valid_coordinates[0]},{valid_coordinates[2]},{valid_coordinates[3]},{valid_coordinates[1]})"
                else:
                    log.info(f"{spatial['type']}")
                    log.info(f"{spatial['coordinates']}")
                    log.info(f"          No spatial bounding box found{('spatial' in dataset and ' in ' + dataset['spatial']) or None}.")
                    envelope = f"ENVELOPE({maxextents_list[0]},{maxextents_list[2]},{maxextents_list[3]},{maxextents_list[1]})"
                
                # send the dataset keywords to a function that parses and returns a standardized list
                # of ISO Topic Keywords
                iso_categories_list = get_iso_topic_categories(dataset["keyword"])

                # send the dataset keywords to a function that parses and returns standardized collection names
                dataset_collections = add_dataset_collections(dataset["keyword"])
                if dataset_collections:
                    collections = dataset_collections + site_collections
                else:
                    collections = site_collections

                # Although not ideal, we use "modified" field for our date
                # ArcGIS Hub's handling of dates is sketchy at best
                # Sometimes modified field is present, but contains invalid data.  We revert to issued date as a last resort.
                if dataset["modified"] != "{{modified:toISO}}":
                    modifiedDate = dataset["modified"]
                else:
                    log.debug(f"          Modified date is missing.")
                    log.debug(f"          Using issued date instead: {dataset['issued']}")
                    modifiedDate = dataset["issued"]

                # Esri DCAT records from Hub make no references to the type of geometry!!
                # For now, we default all of these records to Mixed... no better option
                geomType = "Mixed"

                # create references from distribution
                log.debug(">>>>>>>>>> " + dataset["title"])
                references = "{"
                references += '\"http://schema.org/url\":\"' + dataset["landingPage"] + '\",'
                for refs in dataset["distribution"]:
                    url=getURL(refs)

                    #Fix the encoding of goofy querystring now intrinsic to Esri download links
                    url = url.replace("\"","%22").replace(",","%2C").replace("{","%7B").replace("}","%7D")
                    log.debug(url)

                    # In July 2021, we started seeing distribution formats with null values
                    if refs["format"] is not None:
                        if (refs["format"] == "ArcGIS GeoServices REST API" and url != "invalid"):
                                if ('FeatureServer') in url:
                                    references += '\"urn:x-esri:serviceType:ArcGIS#FeatureLayer\":\"'  + url +  '\",'
                                    log.debug("Found featureServer")
                                elif ('ImageServer') in url:
                                    references += '\"urn:x-esri:serviceType:ArcGIS#ImageMapLayer\":\"'  + url +  '\",'
                                    log.debug("Found ImageServer")
                                elif ('MapServer') in url:
                                    references += '\"urn:x-esri:serviceType:ArcGIS#DynamicMapLayer\":\"'  + url +  '\",'
                                    log.debug("Found MapServer Layer")
                        # Removing download links which are unreliable as of June 2024 due to how
                        # Esri has chosen to implement the Esri DCAT-US standard. 
                        # elif (refs["format"] == "ZIP" and url != "invalid"):
                        #    references += '\"http://schema.org/downloadUrl\":\"' + url + '\",'
                references += "}"
                references = references.replace(",}", "}")
                dc_creator_sm = []
                dc_creator_sm.append(createdBy)
                dct_temporal_sm = []
                dct_temporal_sm.append(modifiedDate[0:4])

                # format gbl record
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
                    "uw_notice_s": "This dataset was automatically cataloged from the author's Open Data Portal. In some cases, publication year and bounding coordinates shown here may be incorrect. Please check the 'More details at' link for additional information including download options.",
                }

                # dump the generated GBL record to a file
                outFileName = identifier
                with open(path + "\\" + outFileName + ".json", 'w') as jsonfile:
                    json.dump(gbl, jsonfile, indent=1)
            else:
                log.info(f"Skipping dataset: {dataset['title']}")
        else:
            if dataset['title'] == "{{name}}":
                log.info(f"Validity check failed on: {dataset['identifier']}.  No title found.")
                log.info(msg)
            else:
                log.info(f"Validity check failed on: {dataset['title']}")
                log.info(msg)

@t.retry(retry=t.retry_if_exception_type((Timeout,HTTPError,),),
         wait=t.wait_exponential_jitter(initial=3.0, max=10.0, jitter=1.0),
         stop=t.stop_after_attempt(5),
         after=lambda x: log.info("Retrying..."))
         
def getSiteJSON(siteURL, session):
    global report_target
    try:
        resp = session.get(siteURL, timeout=30)
    except SSLError:
        resp = session.get(siteURL, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.json()

def read_json_files(folder_path):
    global report_target
    json_pattern = os.path.join(folder_path, '**', '*.json')
    file_list = glob.glob(json_pattern, recursive=True)
    all_json_data = [] #collect all json data

    for json_filename in file_list:
        try:
            with open(json_filename, 'r') as f:
                json_data = json.load(f)
                all_json_data.append(json_data)  # Append data to the list
        except (ValueError, FileNotFoundError) as e:
            log.info(f"Error processing {json_filename}: {e}")   
    return(all_json_data)

def escape_query(raw_query):
    # Uncertain if this is really necessary
    return raw_query.replace("'", "\'")

def add_collection(solr,data,solr_url):
    try:
        solr.add(data)
        return True
    except pysolr.SolrError as e:
        log.info("\n\n*********************")
        log.info("Solr Error: {e}".format(e=e))
        add_to_report("Solr Error: {e}".format(e=e))
        log.info("*********************\n")
        add_to_report("Add Collection to Solr:")
        add_to_report(f"     **** Solr error: {solr_url}\n")
        return False

def delete_collection(solr,collection,solr_url):
    try:
        solr.delete(q=escape_query('dct_isPartOf_sm:"{}"'.format(collection)))
        return True
    except pysolr.SolrError as e:
        log.info("\n\n*********************")
        log.info("Solr Error: {e}".format(e=e))
        add_to_report("Solr Error: {e}".format(e=e))
        log.info("*********************\n")
        add_to_report("\nDelete Solr Collection:")
        add_to_report(f"     **** Solr error: {solr_url}\n")
        return False
        
def add_to_report(message, activate_report=True):
    global produce_report
    if activate_report:
        produce_report = True
    print(message, file=report_target)

log = None
produce_report = False
report_target = StringIO("")
def main():
    try:
        global log, report_target, produce_report
        
        ap = ArgumentParser(description='''Scans ESRI hub sites for records''')
        ap.add_argument('--config-file', default=r"opendata.yml", help="Path to configuration file")
        ap.add_argument('--secrets-file', default=r"secrets.yml", help="Path to secret configuration file! Do not commit to version control!")
        args = ap.parse_args()
        session = requests.Session()
        
        # YAML configuration file
        with open(args.config_file) as stream:
            theDict = yaml.load(stream)
        
        if os.path.exists(args.secrets_file):
            with open(args.secrets_file) as stream:
                theDict |= yaml.load(stream)
                
        log = logging.getLogger(__file__)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        log.addHandler(handler)
        
        # default log level is info
        levelname = theDict.get('log_level', 'INFO').upper()   
        if levelname not in {'CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'}:
            raise RuntimeError('configuration error: {levelname} is not a log level in Python')
        log.setLevel(getattr(logging, levelname))
        
        log.info("\nStarting ArcGIS Hub scanner....")
        log.info("\nLogging level is set to " + levelname)

        # Subfolders for scanned sites will be dumped here
        output_basedir = theDict.get('output_basedir')

        # Clean out existing files from output folder
        sub_folders_pattern = f'{output_basedir}*\\'
        sub_folders_list = glob.glob(sub_folders_pattern)
        for sub_folder in sub_folders_list:
            shutil.rmtree(sub_folder)
        
        # loop through each site in OpenData.yml and call json2gbl function
        for siteCode in theDict["Sites"]:
            site = theDict["Sites"][siteCode]
            log.info("\nProcessing Site: " + siteCode)
            add_to_report(f"\nSite {siteCode}:", activate_report=False)
            site_data = None
            try:
                site_data = getSiteJSON(site['SiteURL'], session)
            except Exception as e:
                log.info(str(e))
                log.info("     Site Failure, check URL")
                add_to_report("     Site Failure, check URL")
                continue
            log.debug(site["SiteURL"])
            json2gbl(site_data, site["CreatedBy"], site["SiteName"], site["Collections"],site["DatasetPrefix"],site["DatasetPostfix"],site["SkipList"],site["MaxExtent"].split(','),output_basedir)
        
        # Should we push the records to Solr?
        if theDict["Solr"]["solr_ingest"]:
            log.info("\nReady to ingest records...")      
            auth = HTTPBasicAuth(theDict["solr_username"],theDict["solr_password"])
            solr_url = theDict["Solr"]["solr_url"]
            solr = pysolr.Solr(solr_url, always_commit=True, timeout=180, auth=auth) 
            collection = theDict["Solr"]["collection"]
            log.info(f"\nDeleting existing {collection}...")
            delete_collection(solr,collection,solr_url)
            json_data = read_json_files(output_basedir)
            log.info("\nPushing new data to Solr...") 
            add_collection(solr,json_data,solr_url)
            
        # Produce and send report if triggered
        if 'report_folder' in theDict and produce_report:
            now = datetime.now().strftime("%Y-%m-%d-%H%M")
            report_file = f"{theDict['report_folder']}scanlog_{now}.txt"
            with open(report_file, 'w') as file:
                file.write(report_target.getvalue())
        
        if 'report_email' in theDict and produce_report:
            port = theDict['report_email'].get('port', 25)
            smtp_server = theDict['report_email']['smtp_server']
            sender_email = theDict['report_email']['sender_email']
            receiver_email = theDict['report_email']['receiver_email']
            email_subject = theDict['report_email']['email_subject']
            message = 'Subject: {}\n\n{}'.format(email_subject, report_target.getvalue())

            with smtplib.SMTP(smtp_server, port) as server:
                server.sendmail(sender_email, receiver_email, message)

    except Exception as e:
        log.info(f"A fatal error occurred: {e}")
        traceback.print_exc()
        add_to_report("***** Fatal error with GeoData@Wisconsin Hub Scanner *****")

        # Produce and send report if triggered
        if 'report_folder' in theDict and produce_report:
            now = datetime.now().strftime("%Y-%m-%d-%H%M")
            report_file = f"{theDict['report_folder']}scanlog_{now}.txt"
            with open(report_file, 'w') as file:
                file.write(report_target.getvalue())
        
        if 'report_email' in theDict and produce_report:
            port = theDict['report_email'].get('port', 25)
            smtp_server = theDict['report_email']['smtp_server']
            sender_email = theDict['report_email']['sender_email']
            receiver_email = theDict['report_email']['receiver_email']
            email_subject = theDict['report_email']['email_subject']
            message = 'Subject: {}\n\n{}'.format(email_subject, report_target.getvalue())

            with smtplib.SMTP(smtp_server, port) as server:
                server.sendmail(sender_email, receiver_email, message)

        sys.exit(1)

if __name__ == '__main__':
    main()