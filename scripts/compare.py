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

# with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json', 'rb') as json_data:
#     d = json.load(json_data)
# with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare.json', 'wb') as fout:
#     json.dump(d, fout, indent=1)
#     os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test.json')

# Open file for reading in text mode (default mode)
f1 = open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_parse.json')
f2 = open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_parse2.json')

# Read the first line from the files
f1_line = f1.readline()
f2_line = f2.readline()

# Initialize counter for line number
line_no = 1
changes = ""
# Loop if either file1 or file2 has not reached EOF
while f1_line != '' or f2_line != '':

    # Strip the leading whitespaces
    f1_line = f1_line.rstrip()
    f2_line = f2_line.rstrip()
    
    # Compare the lines from both file
    if f1_line != f2_line:
        
        # If a line does not exist on file2 then mark the output with + sign
        if f2_line == '' and f1_line != '':
            changes += "Old Data, Line-%d" % line_no + "  " + f1_line + "\n"
        # otherwise output the line on file1 and mark it with > sign
        elif f1_line != '':
            changes += "Old Data, Line-%d" % line_no + "  " + f1_line + "\n"
        # If a line does not exist on file1 then mark the output with + sign
        if f1_line == '' and f2_line != '':
            changes += "New Data, Line-%d" % line_no + "  " + f2_line + "\n"
        # otherwise output the line on file2 and mark it with < sign
        elif f2_line != '':
            changes += "New Data, Line-%d" % line_no + "  " + f2_line + "\n"
        # Print a blank line

    #Read the next line from the file
    f1_line = f1.readline()
    f2_line = f2.readline()


    #Increment line counter
    line_no += 1

print changes



# Close the files
f1.close()
f2.close()
# os.remove('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_compare.json')
# if (len(changes) > 7):
    # with open('C:\\PROJECTS\\Directed_Studies\\DCAT_Test_Data\\test_parse.json', 'wb') as replace:
        # json.dump(d, replace, indent=1)

    # me = "bsegal2@wisc.edu"
    # you = "ben.segal7@gmail.com"
    # s = smtplib.SMTP('localhost')
    # s.sendmail(me,me,changes)
    # s.quit()
