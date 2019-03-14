import json
from pprint import pprint
import urllib
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

now = datetime.datetime.now()
rawmonth = now.month
if rawmonth < 10: month = "0" + str(rawmonth)
else: month = str(rawmonth)
rawday = now.day
if rawday < 10: day = "0" + str(rawday)
else: day = str(rawday)
year = str(now.year)
date = month + "_" + day + "_" + year
print date


testfile = urllib.URLopener()
testfile.retrieve('https://data-ltsb.opendata.arcgis.com/data.json', "C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json")

with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json', 'rb') as json_data:
    d = json.load(json_data)
    slim_json = []
    for x in d["dataset"]:
        temp_obj = {
            "issued":   x["issued"],
            "modified":  x["modified"],
            "title":   x["title"],
            "identifier": x["identifier"]
        }
        slim_json.append(temp_obj)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\compare.json', 'wb') as fout:
    json.dump(slim_json, fout, indent=1)
    os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json')

# Open file for reading in text mode (default mode)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\compare.json') as old_data:
    old = json.load(old_data)
with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\most_recent.json') as new_data:
    new = json.load(new_data)

modDate = "\nThe date(s) on the following layer(s) has/have been updated: \n"
modTitle = "\nThe titles on the following layer(s) has/have changed, but the identifier remains the same: \n"
modID = "\nThe identifier on the following layer(s) has/have changed, but the title remains the same: \n"
modRemoved = "\nThe following layer(s) has/have been removed from the dataset: \n"
modAdded = "\nThe following layer(s) has/have been added to the dataset: \n"
dateCheck = False
titleCheck = False
idCheck = False
remCheck = False
addCheck = False
emailCheck = False
for i in old:
    check = False 
    check2 = False
    for j in new:
        if ( i["identifier"] == j["identifier"]):
            check = True
            if(i["title"] != j["title"]):
                modTitle += "   " + "Identifier: " + i["identifier"] + "\n"
                emailCheck = True
                titleCheck = True
            if (i["issued"] != j["issued"]):
                modDate += "   " + i["title"] + " Issue date \n"
                emailCheck = True
                dateCheck = True
            if (i["modified"] != j["modified"]):
                emailCheck = True
                modDate += "   " + i["title"] + " Modified date \n"
                dateCheck = True
    if check == False:
        for k in new: 
            if(i["title"] == k["title"] and i["identifier"] != k["identifier"]):
                check2 = True
                modID += "   " + i["title"] + "\n"
                emailCheck = True
                idCheck = True
        if check2 == False:
            modRemoved += "   " + i["title"] + "\n"
            emailCheck = True
            remCheck = True

for x in new:
    check3 = False
    for y in old:
        if (x["identifier"] == y["identifier"]  or  x["title"] == y["title"]):
            check3 = True
    if check3 == False:
        modAdded += "   " + x["title"] + "\n"
        emailCheck = True
        addCheck = True

emailMessage = ""
if (addCheck): emailMessage += modAdded
if (remCheck): emailMessage += modRemoved
if (dateCheck): emailMessage += modDate
if (titleCheck): emailMessage += modTitle
if (idCheck): emailMessage += modID



# https://kb.wisc.edu/helpdesk/page.php?id=28139
# port 587
# smtp.office365.com
os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\compare.json')
if (emailCheck == True):
    you = "bsegal2@wisc.edu"
    me = "geodata_sco@wisc.edu" 
    s = smtplib.SMTP('smtp.office365.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login("geodata_sco@wisc.edu", "gBL45??!")
    msg = MIMEMultipart()
    msg['From'] = 'geodata_sco@wisc.edu'
    msg['To'] = 'bsegal2@wisc.edu'
    msg['Subject'] = 'LTSB Changes'
    msg.attach(MIMEText(emailMessage,'plain'))
    s.sendmail(me,you,msg.as_string())
    s.quit()
    with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\ltsb_data_' + date + '.json', 'wb') as replace:
        json.dump(slim_json, replace, indent=1)
    os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\most_recent.json')
    with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\most_recent.json', 'wb') as replace:
        json.dump(slim_json, replace, indent=1)
