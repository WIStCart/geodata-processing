"""
process3dep.py

Purpose: Query the USGS Sciencebase catalog via their Python API to retrieve a specified set of records, and output those records to GeoBlacklight json files.

Author: Jim Lacy, University of Wisconsin-Madison

Thanks to Dell Long and Drew ? from the US Geological Survey Fort Collins Science Center for providing code samples and guidance!

"""

from sciencebasepy import SbSession
import json
from datetime import datetime
import uuid

####### Define constants used for all items

# pick one of the following base IDs
base_item_id = "543e6b86e4b0fd76af69cf4c"  # 3DEP 1-Meter

outputfolder = "r:/scripts/collections/USGS_3dep/gbl/"  # be sure to incude trailing slash
extent_id = 20  # Sciencebase ID for Wisconsin.  No idea how they come up with these state IDs.  Not FIPS.
fields = "identifiers,title,webLinks,id,body,dates,spatial" # fields to retrieve in query
maxRecords = 100  # Max number of records to query at a time.  There is a hard limit of 1000 enforced by Sciencebase.

dct_isPartOf_sm = ["USGS Digital Elevation Data"]   # are these data part of a collection?  
dc_rights_s = "Public"
dc_format_s = "DEM"
dc_type_s = "Dataset"
layer_geom_type_s = "Raster"
dct_provenance_s = "U.S. Geological Survey" # could be retrieved from json response, but this works
dc_creator_sm = ["U.S. Geological Survey"]
dc_publisher_sm = ["U.S. Geological Survey"]
dc_language_s = "English"
dc_subject_sm = ["Elevation"]
dct_spatial_sm = [""]   # We don't use spatial keywords at UW

# fields unique to University of Wisconsin
uw_deprioritize_item_b = True  # we want topo records to appear lower in search results so they don't overwhelm other items
uw_supplemental_s = ""
uw_notice_s = ""
# end University of Wisconsin

###### End of constants

# Begin processing
sb = SbSession()  # create a new session

print("Processing...")
# Send query to Sciencebase and store json response in "items"
# See https://github.com/usgs/sciencebasepy/blob/master/Searching%20ScienceBase%20with%20ScienceBasePy.ipynb for syntax guidance
items = sb.find_items({'ancestors': base_item_id,'filter': 'extentQuery={"extent":' + str(extent_id) + '}','fields':fields,'max': maxRecords})
#print("Found %s items" % items['total'])

while items and 'items' in items:
    for item in items['items']:
        #print(item)    
        for i_link in item['webLinks']:
            try:
                if i_link['type']=='download':
                    downloadUrl = i_link['uri']
            except:
                downloadUrl = ''
            # Geoblacklight currently only supports one download per item
            # future: include GeoTIFFs when they are available
            """try:
                if i_link['title'] == 'GeoTIFF':
                    downloadUrl = i_link['uri']
            except:
                downloadUrl = '' """
            try:
                if i_link['type'] == 'browseImage':
                    thumbnail_path_ss = i_link['uri']
            except:
                thumbnail_path_ss = ''
            try:
                if i_link['type'] == 'Online Link':
                    onlinelink = i_link['uri']
            except:
                onlinelink = ''
        
        for metadata_link in item['identifiers']:
            try:
                #print(metadata_link)
                if metadata_link['scheme'] == 'processingUrl':
                    metadataUrl = metadata_link['key']
            except:
                metadataUrl = ''

        dct_references_s = '{"http://schema.org/url":"%s","http://schema.org/downloadUrl":"%s","http://www.opengis.net/cat/csw/csdgm":"%s"}' % (onlinelink,downloadUrl,metadataUrl)
       
        for date in item['dates']:
            try:
                if date['type'] == 'Start':
                    pubdate = date['dateString']
                    if len(pubdate) == 4:
                        # assume field only contains a year in length of date is four characters
                        year = int(pubdate)
                        #print(year)
                    else:
                        fulldate = datetime.strptime(pubdate, '%Y-%m-%d')
                        year = int(datetime.strftime(fulldate,'%Y'))
                        #print(year)
            except:
                year = 9999    
        
        for boundingBox, coordinates in item['spatial'].items():
                #print(coordinates)
                #for key in coordinates:
                #    print(key + ':', coordinates[key])
                east = coordinates['maxX']
                west = coordinates['minX']
                north = coordinates['maxY']
                south = coordinates['minY']  

        solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (west, east, north, south)

        ###### Construct json object for our GBL record
        uniqueID = str(uuid.uuid4())
        data = {}
        data["geoblacklight_version"] = "1.0"
        data["dc_identifier_s"] = uniqueID
        data["dc_title_s"] = item['title']
        data["dc_description_s"] = item['body']
        data["dc_rights_s"] = dc_rights_s
        data["dct_provenance_s"] = dct_provenance_s
        data["dc_format_s"] = dc_format_s
        data["dc_language_s"] = dc_language_s  
        data["layer_slug_s"] =  uniqueID
        data["layer_geom_type_s"] =  layer_geom_type_s
        data["dct_isPartOf_sm"] = dct_isPartOf_sm
        data["dc_creator_sm"] = dc_creator_sm
        data["dc_publisher_sm"] = dc_publisher_sm
        data["dc_type_s"] = dc_type_s
        data["dc_subject_sm"] = dc_subject_sm
        data["dct_spatial_sm"] = dct_spatial_sm
        data["dct_temporal_sm"] = [str(year)]
        data["solr_geom"] = solr_geom
        data["solr_year_i"] = year
        data["dct_issued_s"] = str(year)
        data["dct_references_s"] = dct_references_s
        # fields unique to University of Wisconsin
        data["thumbnail_path_ss"] = thumbnail_path_ss
        data["uw_supplemental_s"] = uw_supplemental_s
        data["uw_notice_s"] = uw_notice_s
        data["uw_deprioritize_item_b"] = uw_deprioritize_item_b
        # end of UW fields

        outfile = outputfolder + "%s.json" % (uniqueID) # files named by UUID
        out = json.dumps(data,indent=4)
        jsonfile = open(outfile, 'w')
        jsonfile.write(out)
        jsonfile.close()

    items = sb.next(items)  #grab the next set of results, and continue