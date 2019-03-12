import json
from pprint import pprint
import urllib
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



testfile = urllib.URLopener()
testfile.retrieve('https://data-ltsb.opendata.arcgis.com/data.json', "C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json")

with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json', 'rb') as json_data:
    d = json.load(json_data)
    slim_json = []
    for x in d["dataset"]:
        temp_obj = {
            "issued":   x["issued"],
            "modified":  x["modified"],
            "title":   x["title"]
        }
        slim_json.append(temp_obj)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare.json', 'wb') as fout:
    json.dump(slim_json, fout, indent=1)
    os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json')

# Open file for reading in text mode (default mode)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare.json') as old_data:
    old = json.load(old_data)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare2.json') as new_data:
    new = json.load(new_data)

missing = []
for i in old:
    for j in new:
        if ( i["title"] == j["title"]):
            # print i["issued"] + "   " + j["issued"]
            if (i["issued"] != j["issued"]):
                print "Issue date has changed for " + i["title"]
            if (i["modified"] != j["modified"]):
                print "Modified date has changed for " + i["title"]

# https://kb.wisc.edu/helpdesk/page.php?id=28139
# port 587
# smtp.office365.com
#
# os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare.json')
# if (len(changes) > 7):
    # with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_parse.json', 'wb') as replace:
    #     json.dump(d, replace, indent=1)
    # from email.mime.multipart import MIMEMultipart
    # me = "bsegal2@wisc.edu"
    # you = "geodata@sco.wisc.edu" 
    # s = smtplib.SMTP('smtp.office365.com', 587)
    # s.ehlo()
    # s.starttls()
    # s.login("bsegal2@wisc.edu", "Al15@jlm")
    # msg = MIMEMultipart()
    # msg['From'] = 'bsegal2@wisc.edu'
    # msg['To'] = 'bsegal2@wisc.edu'
    # msg['Subject'] = 'LTSB Changes'
    # msg.attach(MIMEText(changes,'plain'))
    # s.sendmail(me,me,msg.as_string())
    # s.quit()
