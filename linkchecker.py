"""
This script connects to a defined Solr database and pulls back a list of URLs to check for errors.  This is used to QA/QC the information held in GeoData@Wisconsin records.
Author: Jim Lacy
Date: January 2025 
"""

# External python libraries follow
# requires additional installation
# python -m pip install -r linkchecker.txt

import json
import os
import sys
import csv
import re
import pysolr
from argparse import ArgumentParser
from ruamel.yaml import YAML
from requests.auth import HTTPBasicAuth
from colorama import Back, Style, init
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import urlparse
from datetime import datetime
import requests
import aiohttp
import asyncio

yaml = YAML()
interactive = True

def check_urls(checklist):
    # This is the "normal" method for checking a list of urls.  This is slow, but is more reliable in that it tends to not overwhelm the target servers as easily. As an added 
    # benefit, valid links are only checked once... subsequent instances of the same link are skipped. As of January 2025, this methods requires aboutt three hours to check all
    # links in GeoData@Wisconsin.
    global interactive
    checkedurls = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.sco.wisc.edu'}
    for item in checklist:
        if item["url"] not in checkedurls:
            try:
                response = requests.head(item["url"],headers=headers,timeout=5,allow_redirects=True)
            except requests.exceptions.HTTPError as e:
                item["status"] = "Error"
                if interactive: print(f"{item['url']} {Back.RED}{e}{Style.RESET_ALL}")
            except requests.exceptions.ConnectionError as e:
                item["status"] = "Error"
                if interactive: print(f"{item['url']} {Back.RED}{e}{Style.RESET_ALL}")
            except requests.exceptions.Timeout as e:
                item["status"] = "Error" 
                if interactive: print(f"{item['url']} {Back.RED}{e}{Style.RESET_ALL}")
            except requests.exceptions.SSLError as e:
                item["status"] = "Error"
                if interactive: print(f"{item['url']} {Back.RED}{e}{Style.RESET_ALL}")
            except requests.exceptions.RequestException as e:
                item["status"] = "Error"
                if interactive: print(f"Unexpected Error: {item['url']} {Back.RED}{e}{Style.RESET_ALL}")
            else:
                item["status"] = response.status_code
                if response.status_code != 200:
                    # note that we do NOT add url to checkedurls when a bad link is found.  This is because we want all instances of the url to be double-checked and flagged
                    if interactive: print(f"{item['url']} {Back.RED}{item['status']}{Style.RESET_ALL}")
                else:
                    if interactive: print(f"{item['url']} {Back.GREEN} {item['status']}{Style.RESET_ALL}")
                    # this url worked, so no need to check it again
                    checkedurls.append(item["url"])
    return(checklist)


# Note that this method does not keep track of urls already checked.  This is because the async nature of the processing proved this to be very difficult and unreliable.
# The "async" method is extremely fast, but it can sometimes overwhelm target servers and potentially lead to being flagged as a DDoS attack. 
async def check_url_async(session,item):
    global interactive

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.sco.wisc.edu'}
    url = item["url"]
    try:
        # note the following craps out when attempting to set a timeout value.
        async with session.head(url,headers=headers,allow_redirects=True) as response:
            item["status"] = response.status
    except aiohttp.ClientError as e:
        item["status"] = "Error"
        if interactive: print(f"{url} {Back.RED}{e}{Style.RESET_ALL}")
    except Exception as e:
        item["status"] = "Error"
        if interactive: print(f"Unexpected Error: {url} {Back.RED}{e}{Style.RESET_ALL}")
    else:
        if response.status != 200:
            if interactive: print(f"{url} {Back.RED}{item['status']}{Style.RESET_ALL}")
        else:
            if interactive: print(f"{url} {Back.GREEN} {item['status']}{Style.RESET_ALL}")
    finally:
        return item

# assemble the async job, and run it
async def check_all_urls_async(checklist):
    async with aiohttp.ClientSession() as session:
        tasks = [check_url_async(session, item) for item in checklist]
        results = await asyncio.gather(*tasks)
        return results

# Regular expression pattern to match URLs
# This is used to find urls in long strings of text
def extract_urls(text):
    url_pattern = r'https://[^\s]+|https://[^\s]+'
    matches = re.findall(url_pattern, text)
    return matches

# look for extra characters that sometimes get attached to end of actual urls.  This is common when
# extracting urls from dc_description_s. Furthermore, sometimes the checker returns an error if the site ends
#  with a /, such as https://sco.wisc.edu/
def strip_end_chars(input_string):
    while input_string.endswith(']') or input_string.endswith('.') or input_string.endswith(')') or input_string.endswith("'") or input_string.endswith(",") or input_string.endswith("/") or input_string.endswith(" "):
        input_string = input_string[:-1]  # Remove the last character
    return input_string

# construct and send email
def send_email(configDict, processing_time, filename):
    port = configDict['report_email'].get('port', 25)
    smtp_server = configDict['report_email']['smtp_server']
    sender_email = configDict['report_email']['sender_email']
    receiver_email = configDict['report_email']['receiver_email']
    email_subject = configDict['report_email']['email_subject']
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = email_subject
    
    msg.attach(MIMEText(f'Total processing time: {processing_time}', 'plain'))
    attachment = open(filename, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())

    # Encode into base64
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(filename)}")

    # Attach the instance 'part' to instance 'msg'
    msg.attach(part)
    
    # Close the file
    attachment.close()

    with smtplib.SMTP(smtp_server, port) as server:
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)

def main():
    global interactive

    # setup input arguments.
    ap = ArgumentParser(description='''Check Solr database for bad urls.''')
    ap.add_argument('-c','--config-file', default=r"linkchecker.yml", help="Path to configuration file")
    ap.add_argument('-s','--secrets-file', default=r"secrets.yml", help="Path to secret configuration file. Do not commit to version control!")
    ap.add_argument('-o','--output-file', default=r"output.csv", help="Path to output csv file with link check results.")
    ap.add_argument('-i','--instance', default=r"test", help="Which Solr database to use: prod, dev, or test")
    ap.add_argument('-m','--mode', default=r"interactive", help="interactive or batch.  Batch mode does not print output to screen.")
    ap.add_argument("method",choices=["async","normal"],help="async or normal. Async is very fast, but can overwhelm target servers.") 
    args = ap.parse_args()

    # YAML configuration files
    if os.path.exists(args.config_file):
        with open(args.config_file) as stream:
            configDict = yaml.load(stream) 
    if os.path.exists(args.secrets_file):
        with open(args.secrets_file) as stream:
            configDict |= yaml.load(stream)

    # set Solr Url based on config file           
    if args.instance == 'prod':
        solr_url = configDict["Solr"]["prod"]
    elif args.instance == 'test':
        solr_url = configDict["Solr"]["test"]
    else:
        solr_url = configDict["Solr"]["dev"]  
    
    # are we outputting stuff to the screen?
    if args.mode == "interactive":
        interactive = True
    else:
        interactive = False
    
    # What method of operation are we using? Async runs much faster. 
    if args.method == "async":
        method = "async"
    else:
        method ="normal"

    init() # initialize colorama, used for highlighting text in interactive mode

    if interactive: print("\nStarting GeoData link checker....\n")
    if interactive: print(f"Querying {solr_url}...\n")

    # create a new list that holds the sites we should skip
    skipdict = configDict["skip"]
    skiplist = []
    for skipurl in skipdict:
        if interactive: print(f"Skipping {skipurl['url']}....")
        skiplist.append(skipurl["url"])

    query = '*:*'
    auth = HTTPBasicAuth(configDict["solr_username"],configDict["solr_password"])
    solr = pysolr.Solr(solr_url, always_commit=True, timeout=180, auth=auth)
   
    # run the solr query
    try:
        results = solr.search(query,rows=100000)  
    except pysolr.SolrError as e:
        print("\n\n*********************")
        print("Solr Error: {e}".format(e=e))
        print("*********************\n")
        sys.exit(1)

    # Read through all documents returned from Solr, and extract urls from dct_references_s, uw_supplemental_s, and dc_description_s
    # Constructs a dictionary for every link found
    checklist=[]
    if interactive: print(f"Number of solr records returned: {len(results)}") 
    #loop through each item returned from Solr search
    for result in results:         
        # create an empty list to store all URLs found in dct_references_s
        referencelist=[]
        
        # do we have any links to check in dct_references_s?
        if "dct_references_s" in result:
            data = json.loads(result["dct_references_s"])
            #split everything into keys and values
            references = {key: value for key, value in data.items()}
            
            # loop through all of the references found in DCT references
            # downloadUrl can have multiple links or a single link, which makes things more complicated
            for key, url in references.items():                   
                if key == "http://schema.org/downloadUrl": 
                    # Is this a multi-download reference?
                    if isinstance(url,list):
                        # loop thru urls in multi-download list, add each to our reference list
                        for link in url:
                            referencelist.append(link['url'])
                    else:
                        # just a single link to append to reference list
                        referencelist.append(url)
                else:
                    # reference type is not download
                    referencelist.append(url)
        
            # now loop thru entire list of urls found so far, construct the dict object.
            # Note that initial status is set to 0.  
            for reference in referencelist:
                if "dct_isPartOf_sm" in result:
                    dct_isPartOf_sm = result["dct_isPartOf_sm"]
                else:
                    dct_isPartOf_sm = ""
                dict={"dc_identifier_s":result["dc_identifier_s"],
                "dc_title_s":result["dc_title_s"],
                "dct_provenance_s":result["dct_provenance_s"],
                "dct_isPartOf_sm":dct_isPartOf_sm,
                "url": strip_end_chars(reference),
                "source":"dct_references_s",
                "status":0}
                checklist.append(dict)
        
        # look in uw_supplemental_s, pull out more urls to check
        if "uw_supplemental_s" in result:
            urls = extract_urls(result["uw_supplemental_s"])
            if urls:
                for url in urls:
                    if "dct_isPartOf_sm" in result:
                        dct_isPartOf_sm = result["dct_isPartOf_sm"]
                    else:
                        dct_isPartOf_sm = ""
                    dict={"dc_identifier_s":result["dc_identifier_s"],
                    "dc_title_s":result["dc_title_s"],
                    "dct_provenance_s":result["dct_provenance_s"],
                    "dct_isPartOf_sm":dct_isPartOf_sm,
                    "url":strip_end_chars(url),
                    "source":"uw_supplemental_s",
                    "status":0}
                    checklist.append(dict)
        
        # look in dc_description_s, pull out urls to check     
        if "dc_description_s" in result:
            urls = extract_urls(result["dc_description_s"])
            if urls:
                for url in urls:
                    if "dct_isPartOf_sm" in result:
                        dct_isPartOf_sm = result["dct_isPartOf_sm"]
                    else:
                        dct_isPartOf_sm = ""
                    dict={"dc_identifier_s":result["dc_identifier_s"],
                    "dc_title_s":result["dc_title_s"],
                    "dct_provenance_s":result["dct_provenance_s"],
                    "dct_isPartOf_sm":dct_isPartOf_sm,
                    "url":strip_end_chars(url),
                    "source":"dc_description_s",
                    "status":0}
                    checklist.append(dict)
        
    # Use list comprehension to remove links that are part of the open data collection.
    # We don't bother checking open data links since they update daily  
    checklist[:] =  [item for item in checklist if 'Wisconsin Open Data Sites' not in item["dct_isPartOf_sm"]]

    # Remove urls defined in config file
    checklist[:] = [
        item for item in checklist 
        if urlparse(item["url"]).scheme + "://" + urlparse(item["url"]).netloc not in skiplist
    ]
    
    if interactive: print(f"Number of links to check: {len(checklist)}")
    
    # sort the list. This is not critical, and doesn't matter much especially when using async method
    sorted_checklist = sorted(checklist,key=lambda x: x["url"]) 
    
    checkedlist = []
    start_time = datetime.now()
    if interactive: print(f"Started link checks at {start_time.strftime('%H:%M:%S')}.")
    if method == "async":
        checkedlist = asyncio.run(check_all_urls_async(sorted_checklist)) # async method
    else:
        checkedlist = check_urls(sorted_checklist) # standard method
    end_time = datetime.now()
    processing_time = end_time-start_time
    if interactive: print(f"Finished link checks at {end_time.strftime('%H:%M:%S')}.")
    if interactive: print(f"Total time to process: {processing_time}.")
    
    # use list comprehension to get rid of items that we consider okay 
    # 200: this means the url is working as expected
    # 403: permanent redirect sometimes messes with checker.  We punt and don't worry about it.
    # 405: method not allowed.  Most likely a function of scripted access to a url.  Skip it.
    # 503 service unavailable.  Usually means we overwhelmed the server with requests and/or triggered a security issue. Skip it.
    # 0: link was not checked because it was already checked previously ("normal" method only)
    # Error:  Catch-all category for different types of responses that raise an exception.  Most commonly SSL or timeout errors.
    checkedlist[:] =  [item for item in checkedlist if item["status"] != 200 and item["status"] != 0 and item["status"] != 405 and item["status"] !=403 and item["status"] !=503 and item["status"] != "Error"]
    if interactive: print(f"Found {len(checkedlist)} links that require attention.")
    
    # Output to a csv file
    header = ['dc_identifier_s', 'dc_title_s', 'dct_provenance_s','dct_isPartOf_sm','url','source','status']
    if interactive: print(f"Writing results to {args.output_file}.")
    # by using 'with' the file is automatically closed
    with open(args.output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file,fieldnames=header)
        writer.writeheader()
        writer.writerows(checkedlist)
    
    # send report
    send_email(configDict, processing_time, args.output_file)       

if __name__ == '__main__':
    main()
