# Script to process a CSV list of tiled geographic features, and convert to Geoblacklight metadata
# each new script will need to be modified based on the specific formatting of the input CSV
import csv
import json

#### configure the most common global options needed to process the geoblacklight metadata
inputfile = "WI_NAIP_2015_mosaics.csv"
outputfile = "WI_NAIP_2015_mosaics.json"
title_template = "%s %s County Aerial Mosaic"
dc_description_s = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Gravida rutrum quisque non tellus orci ac auctor augue mauris. Ut etiam sit amet nisl. Etiam tempor orci eu lobortis elementum nibh tellus molestie nunc. Varius quam quisque id diam vel. Pretium viverra suspendisse potenti nullam ac tortor. Sapien pellentesque habitant morbi tristique senectus. Pellentesque habitant morbi tristique senectus et. Arcu dui vivamus arcu felis bibendum ut. Ut sem viverra aliquet eget sit amet. Enim praesent elementum facilisis leo vel. At elementum eu facilisis sed odio morbi quis. Pharetra diam sit amet nisl. Mus mauris vitae ultricies leo. Nec nam aliquam sem et tortor consequat. Quisque egestas diam in arcu cursus euismod quis viverra. Orci phasellus egestas tellus rutrum. In tellus integer feugiat scelerisque varius morbi enim. Nec feugiat nisl pretium fusce. At lectus urna duis convallis convallis tellus id interdum velit. Odio ut sem nulla pharetra diam sit amet nisl suscipit. Neque volutpat ac tincidunt vitae semper quis lectus nulla at."
dct_provenance_s = "WisconsinView"  # where are the data held?
dct_isPartOf_sm = "2015 NAIP Imagery"   # are data part of a collection?  Use standardized collections dictionary!
dc_creator_sm = "USDA Farm Service Agency"   # who created the data?
dc_format_s = "MrSID"  # format of the file
online_linkage_template = "ftp://ftp.ssec.wisc.edu/pub/wisconsinview/NAIP_2015/%s"	
wms_link = "https://realearth.ssec.wisc.edu/cgi-bin/mapserv?map=NAIPWI.map"
layer_id_s =  "NAIPWI_20150701_120000_e26915" # this is the layer name needed for the WMS connection
year = 2015
#### end most common options
		
		
datalist=[] # a list object that contains the data read from CSV
with open(inputfile) as csvfile:
	readCSV = csv.reader(csvfile, delimiter=',')
	for row in readCSV:
		# read each row of the CSV into a dictionary object
		# each dictionary object becomes a single GBL record when exported to JSON later
		data = {}			
			
		# setup variables used to populate dictionary
		# remember that column counter begins at zero, not 1
		# e.g., row[4] refers to the fifth element in the CSV row
		county_link = row[1]
		county_name = row[2]
		online_linkage = online_linkage_template % (county_link)
		dct_references_s = '{"http://schema.org/downloadUrl":"%s","http://www.opengis.net/def/serviceType/ogc/wms":"%s"}' % (online_linkage,wms_link)
		min_x = row[4]
		min_y = row[5]
		max_x = row[6]
		max_y = row[7]
		solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (min_x, max_x, max_y, min_y)
		dc_identifier_s = str(year) + "_" + county_link + "_" + "NAIP_mosaic"		
		
		#limit modifications to the following block of code
		data["geoblacklight_version"] = "1.0"
		data["dc_identifier_s"]= dc_identifier_s
		data["dc_title_s"] = title_template % (year,county_name)
		data["dc_description_s"] = dc_description_s
		data["dc_rights_s"] = "Public"  # all data are public
		data["dct_provenance_s"] = dct_provenance_s
		data["dc_format_s"] = dc_format_s
		data["dc_language_s"] = "English"  # all data are English
		data["layer_slug_s"] =  dc_identifier_s
		data["layer_geom_type_s"] =  "Raster"
		data["layer_id_s"] =  layer_id_s
		data["dct_isPartOf_sm"] = [dct_isPartOf_sm]
		data["dc_creator_sm"] = [dc_creator_sm]
		data["dc_type_s"] = "Dataset"
		data["dc_subject_sm"] = ["Imagery"]
		data["dct_spatial_sm"] = ["Wisconsin", county_name + " County"] 
		data["dct_temporal_sm"] = year
		data["solr_geom"] = solr_geom
		data["solr_year_i"] = year
		data["dct_references_s"] = dct_references_s
		print(data)
		print ("****************************************")
		datalist.append(data)

# Create JSON file from list		
out = json.dumps(datalist)  
jsonfile = open(outputfile, 'w')  
jsonfile.write(out) 
jsonfile.close()







	





