"""
processtopos.py

Purpose: Query the USGS Sciencebase catalog via their Python API to retrieve a specified set of records, and output those records to GeoBlacklight json files.

Author: Jim Lacy, University of Wisconsin-Madison

Thanks to Dell Long and Drew Ignizio from the US Geological Survey Fort Collins Science Center for providing code samples and guidance!

"""

from sciencebasepy import SbSession
import json
from datetime import datetime
from datetime import timezone
import uuid

####### Define constants used for all items

# Could loop through topo collections, but we choose to simply run the script twice (once per topo collection)
# pick one of the following base IDs

#base_item_id = "4f554260e4b018de15819c88"  # All Historic Topographic Maps (pre-US Topo) 
base_item_id = "4f554236e4b018de15819c85"  # US Topos 

# The following is redundant, and should not be used.  Item 4f554236e4b018de15819c85 already contains historic US Topos in addition to current topos
#base_item_id = "5061bc99e4b0ce47085a8d03"  # US Topos Historical

outputfolder = "r:/scripts/collections/USGS_Topos/gbl/"  # be sure to incude trailing slash
extent_id = 20  # Sciencebase ID for Wisconsin.  No idea how they come up with these state IDs.  Not FIPS.
fields = "identifiers,title,webLinks,id,body,dates,spatial" # fields to retrieve in query
maxRecords = 100  # Max number of records to query at a time.  There is a hard limit of 1000 enforced by Sciencebase.
now = datetime.now(timezone.utc) # used to populate layer_modified_dt, which must be in UTC
dct_isPartOf_sm = ["USGS Topographic Maps"]   # are these data part of a collection?  
dc_rights_s = "Public"
dc_type_s = "Dataset"
layer_geom_type_s = "Image"
dct_provenance_s = "U.S. Geological Survey" # could be retrieved from json response, but this works
dc_creator_sm = ["U.S. Geological Survey"]
dc_publisher_sm = ["U.S. Geological Survey"]
dc_language_s = "English"
dc_subject_sm = ["Imagery and Base Maps"]
dct_spatial_sm = [""]   # We don't use spatial keywords at UW

# fields unique to University of Wisconsin
uw_deprioritize_item_b = True  # we want topo records to appear lower in search results so they don't overwhelm other items
uw_notice_s = ""
# end University of Wisconsin

###### End of constants

# Begin processing
sb = SbSession()  # create a new session

print("Processing...")
# Send query to Sciencebase and store json response in "items"
# See https://github.com/usgs/sciencebasepy/blob/master/Searching%20ScienceBase%20with%20ScienceBasePy.ipynb for syntax guidance
items = sb.find_items({'ancestors': base_item_id,'filter': 'extentQuery={"extent":' + str(extent_id) + '}','fields':fields,'max': maxRecords})
print("Found %s items" % items['total'])

while items and 'items' in items:
    for item in items['items']:
        #print(item) 
        onlinelink = "" 
        downloadUrl = "" 
        metadataUrl = ""
        downloadsList = [] # create new list for download links
        references_s = {}
        for i_link in item['webLinks']:
            #print(i_link)               
            if i_link['type'] == 'download':
                downloadUri = i_link['uri']
                label = i_link['title']              
                downloadDict = {'url':downloadUri,'label':label}
                downloadsList.append(downloadDict)
                #print(downloadsList)
            elif i_link['type'] == 'browseImage':
                thumbnail_path_ss = i_link['uri']
                #print("Thumbnail Path: " + thumbnail_path_ss)
            elif i_link['type'] == 'originalMetadata':
                metadataUrl = i_link['uri']
                references_s["http://www.opengis.net/cat/csw/csdgm"] = metadataUrl
                #print("Metadata Url: " + metadataUrl)
            elif i_link['type'] == 'Online Link':
                # hack to account for USGS not updating Sciencebase with correct link to historic topos
                if base_item_id == '4f554260e4b018de15819c88':
                    onlinelink = "https://www.usgs.gov/programs/national-geospatial-program/historical-topographic-maps-preserving-past"
                    #print(onlinelink)
                else:
                    onlinelink = i_link['uri']
                references_s["http://schema.org/url"] = onlinelink
                #print("Online Link: " + onlinelink)
        
        if metadataUrl == '':
        # this means the metadata url was not found in the "weblinks" section, so let's look in identifiers instead
        # no idea why USGS chooses to put the metadata link in different spots!          
            for identifiers in item['identifiers']:
                if identifiers['scheme'] == 'processingUrl':
                    references_s["http://www.opengis.net/cat/csw/csdgm"] = identifiers['key']
                 
        references_s["http://schema.org/downloadUrl"] = downloadsList       
        dct_references_s = json.dumps(references_s)
               
        if len(downloadsList) > 1:
            dc_format_s = "Multiple Formats" # this means both GeoPDF and GeoTIFF are options.  This was suggested by Karen M.
        else:
            #dc_format_s = downloadsList[0]["label"] # This is the more elegant approach, but USGS is inconsistent with labeling of GeoPDF format! ("GeoPDF", "Geospatial PDF")
            dc_format_s = "GeoPDF" 
            
        for date in item['dates']:
            # need to double-check this try-except statement?
            try:
                if date['type'] == 'Publication':
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
                east = coordinates['maxX']
                west = coordinates['minX']
                north = coordinates['maxY']
                south = coordinates['minY']  

        solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (west, east, north, south)
        
        # ugly hack!  The most recent US Topos do not contain a year in the title
        if year >= 2022:    
            title = "%s %s" % (item['title'],year)
        else:
            title = item['title']
        #print(title)   
        
        ###### Construct dictionary for our GBL record
        uniqueID = str(uuid.uuid4())
        data = {}
        data["geoblacklight_version"] = "1.0"
        data["dc_identifier_s"] = uniqueID
        data["dc_title_s"] = title
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
        data["layer_modified_dt"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        data["dct_issued_s"] = str(year)
        data["dct_references_s"] = dct_references_s
        data["thumbnail_path_ss"] = thumbnail_path_ss
        data["uw_notice_s"] = uw_notice_s
        data["uw_deprioritize_item_b"] = uw_deprioritize_item_b

        outfile = outputfolder + "%s.json" % (uniqueID) # files named by UUID
        out = json.dumps(data,indent=4)
        jsonfile = open(outfile, 'w')
        jsonfile.write(out)
        jsonfile.close()

    items = sb.next(items)  #grab the next set of results, and continue