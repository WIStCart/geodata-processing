import csv
import json
from datetime import datetime
from datetime import timezone
outputfolder = 'R:/scripts/collections/wgnhs/gbl'
with open('R:/scripts/collections/wgnhs/WGNHS_GeoData.csv') as file:
    for i in csv.DictReader(file):
        with open('R:/scripts/collections/wgnhs/WGNHS_GBL_template.json', 'r') as openfile:
            # Reading from json file
            json_object = json.load(openfile)
            json_object['dc_identifier_s'] = dict(i)['dc_identifier']
            json_object['dc_title_s'] = dict(i)['dc_title']
            json_object['dc_description_s'] = dict(i)['dc_description']
            json_object['layer_slug_s'] = dict(i)['layer_slug']
            json_object['layer_modified_dt'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            json_object['dc_subject_sm'] = [dict(i)['dc_subject']]
            json_object['dct_temporal_sm'] = dict(i)['dct_temporal']
            json_object['solr_year_i'] = dict(i)['solr_year']
            json_object['dct_references_s'] = '{"http://schema.org/url":"%s","http://schema.org/downloadUrl":"%s"}' % (dict(i)['information_URL'],dict(i)['download_URL'])
            json_object['solr_geom'] = dict(i)['Envelope']
            json_object['uw_supplemental_s'] = dict(i)['uw_supplemental']
            
        with open("{}/{}.json".format(outputfolder,dict(i)['dc_identifier'].replace(" ","_")), "w") as jsonFile:
            json.dump(json_object, jsonFile, indent=1)

