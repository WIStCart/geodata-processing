import json
import csv

# Create 72 Wisconsin county template GBL files
exampleFile = open('countyboundCSV.csv')
exampleReader = csv.reader(exampleFile)
exampleData = list(exampleReader)

for item in exampleData:
    with open('template.json', 'r') as json_file:
        data = json.load(json_file)
        data['dc_title_s'] = item[1]
        data['solr_geom'] = 'ENVELOPE({},{},{},{})'.format(item[2],item[4],item[5],item[3])
    with open("{}.json".format(item[1]), "w") as jsonFile:
        json.dump(data, jsonFile, indent=1)
print("all done")


        
    

