# Script to process a CSV list of tiled geographic features, and convert to Geoblacklight metadata
# each new script will need to be modified based on the specific formatting of the input CSV
import csv
import json

#### configure the most common global options needed to process the geoblacklight metadata
inputfile = "2017naip.csv"
outputfile = "WI_NAIP_2017.json"
outputfolder = ".\\output\\"
title_template = "%s Aerial Image: %s %s Quarter-Quadrangle"
dc_description_s = "This data set contains imagery from the National Agriculture Imagery Program (NAIP). The NAIP acquires digital ortho imagery during the agricultural growing seasons in the continental U.S.. A primary goal of the NAIP program is to enable availability of ortho imagery within one year of acquisition. The NAIP provides two main products: 1 meter ground sample distance (GSD) ortho imagery rectified to a horizontal accuracy within +/- 5 meters of reference digital ortho quarter quads (DOQQ's) from the National Digital Ortho Program (NDOP) or from the National Agriculture Imagery Program (NAIP); 1 meter or 1/2 meter GSD ortho imagery rectified within +/- 6 meters to true ground. The tiling format of NAIP imagery is based on a 3.75' x 3.75' quarter quadrangle with a 300 pixel buffer on all four sides. The NAIP imagery is formatted to the UTM coordinate system using the North American Datum of 1983 (NAD83). The NAIP imagery may contain as much as 10% cloud cover per tile. This file was generated by compressing NAIP imagery that covers the county extent."
dct_provenance_s = "WisconsinView"  # where are the data held?
dct_isPartOf_sm = "Aerial Imagery"   # are data part of a collection?  Use standardized collections dictionary!
dc_creator_sm = "USDA Farm Service Agency"   # who created the data?
dc_format_s = "GeoTIFF"  # format of the file
online_linkage_template = "ftp://ftp.ssec.wisc.edu/pub/wisconsinview/NAIP_2017_t/%s/%s.tif"
metadata_link_template = "ftp://ftp.ssec.wisc.edu/pub/wisconsinview/NAIP_2017_t/%s/%s.txt"	
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
        dc_title_s = row[4]
        date = row[23]
        year = date[0:4]  # example of extracting text from string... positions 0 to 3 (4 items) in this case
        month = date[4:6]
        day = date[6:8]
        filename = row[25]
        index = filename[2:7]
        online_linkage = online_linkage_template % (index,filename[:-13])
        metadata_link = metadata_link_template % (index,filename[:-13])
        # additional external linkages (not used)
        #arcgis_link = "https://dnrmaps.wi.gov/arcgis_image/rest/services/DW_Image/EN_Image_Basemap_Leaf_Off/ImageServer/"	
        #wms_link = "https://realearth.ssec.wisc.edu/cgi-bin/mapserv?map=NAIPWI.map&request=GetCapabilities&service=WMS&version=1.3"
        dct_references_s = '{"http://schema.org/downloadUrl":"%s","http://schema.org/url":"%s"}' % (online_linkage,metadata_link)
        min_x = row[26]
        min_y = row[27]
        max_x = row[28]
        max_y = row[29]
        solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (min_x, max_x, max_y, min_y)
        dc_identifier_s = row[25]

        #limit modifications to the following block of code
        data["geoblacklight_version"] = "1.0"
        data["dc_identifier_s"]= dc_identifier_s[:-4]
        data["dc_title_s"] = title_template % (year,dc_title_s.title()[:-3],dc_title_s[-2:])
        data["dc_description_s"] = dc_description_s
        data["dc_rights_s"] = "Public"  # all data are public
        data["dct_provenance_s"] = dct_provenance_s
        data["dc_format_s"] = dc_format_s
        data["dc_language_s"] = "English"  # all data are English
        data["layer_id_s"] = ""   # not used
        data["layer_slug_s"] =  dc_identifier_s[:-4]
        data["layer_geom_type_s"] =  "Raster" #### imagery?
        data["layer_modified_dt"] = "%s-%s-%sT00:00:00Z" % (year,month,day)  # Solr requires two characters for month and day
        data["dct_isPartOf_sm"] = [dct_isPartOf_sm]
        data["dc_creator_sm"] = [dc_creator_sm]
        data["dc_type_s"] = "Dataset"
        data["dc_subject_sm"] = ["Imagery"]
        data["dct_spatial_sm"] = ["Wisconsin"]   # for NAIP, there is no convenient way to also specify a county
        data["dct_issued_s"] = "%s-%s-%s" % (year,month,day)
        data["dct_temporal_sm"] = year
        data["solr_geom"] = solr_geom
        data["solr_year_i"] = year
        data["dct_references_s"] = dct_references_s
        outfile = outputfolder + dc_identifier_s[:-4] + ".json"
        #print("Output file is: " + outfile)       
        datalist.append(data)
        out = json.dumps(data)
        jsonfile = open(outfile, 'w')
        jsonfile.write(out)
        jsonfile.close()






	




