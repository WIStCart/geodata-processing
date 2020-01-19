# Script to process a CSV list of tiled geographic features, and convert to Geoblacklight metadata
# each new script will need to be modified based on the specific formatting of the input CSV
import csv
import json
import uuid

#### configure the most common global options needed to process the geoblacklight metadata
inputfile = "P:\\scripts\\collections\\wisconsinview\\counties.csv"
outputfolder = "P:\\scripts\collections\wisconsinview\\2008_NAIP_GBL\\"
title_template = "NAIP Aerial Mosaic (UTM) %s County, WI %s"
dc_description_s ="PRELIMINARY 2008 National Agriculture Imagery Program (NAIP). This data set contains imagery from the National Agriculture Imagery Program (NAIP). The NAIP acquires digital ortho imagery during the agricultural growing seasons in the continental U.S.. A primary goal of the NAIP program is to enable availability of ortho imagery within one year of acquisition. INTENDED DISPLAY SCALE: 1:12,000; GROUND RESOLUTION: 1-Meter pixels; ACCURACY: + or - 15 MetersNOTE: This imagery is a Preliminary or 'INTERIM' version of the USDA 2008 NAIP digital orthophotography. According to the USDA, 'Users should be aware that the interim compressed county mosaic may contain defects and have horizontal accuracy less than the specified tolerances. Defective imagery may be replaced within one year of image acquisition date. For more information: http://www.fsa.usda.gov/Internet/FSA_File/naip_2007_infosheetpdf.pdf"
dct_provenance_s = "WisconsinView"  # where are the data held?
dct_isPartOf_sm = ["Aerial Imagery"]   # are data part of a collection?  Use standardized collections dictionary!
dc_creator_sm = "U.S. Department of Agriculture"   # who created the data?
dc_format_s = "MrSID"  # format of the file

# Remember: don't delete the %s
online_linkage_template = "http://bin.ssec.wisc.edu/pub/wisconsinview/NAIP_2008/%s"	
#wms_link = "https://realearth.ssec.wisc.edu/cgi-bin/mapserv?map=NAIPWI.map"
layer_id_s =  "" # this is the layer name needed for the WMS connection
year = 2008
metadata_linkage = "https://gisdata.wisc.edu/public/metadata/wi_naip_2008.xml"
uw_supplemental_s = "This dataset is also available as a mosaic referenced to the Wisconsin Transverse Mercator (WTM) coordinate system."

# Remember: don't delete the %s
filename_template = "%s_%s_NAIP_Mosaic_UTM.json"
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
        county_name = row[1]
        county_folder = row[2]
        online_linkage = online_linkage_template % (county_folder)
        dct_references_s = '{"http://schema.org/url":"https://www.fsa.usda.gov/programs-and-services/aerial-photography/imagery-programs/naip-imagery/","http://schema.org/downloadUrl":"%s","http://www.isotc211.org/schemas/2005/gmd/":"%s"}' % (online_linkage,metadata_linkage)
        west = row[3]
        east = row[4]
        north = row[5]
        south = row[6]
        solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (west, east, north, south)
        dc_identifier_s = str(uuid.uuid4())

        #limit modifications to the following block of code
        data["geoblacklight_version"] = "1.0"
        data["dc_identifier_s"]= dc_identifier_s
        data["dc_title_s"] = title_template % (county_name,year)
        data["dc_description_s"] = dc_description_s
        data["dc_rights_s"] = "Public"  # all data are public
        data["dct_provenance_s"] = dct_provenance_s
        data["dc_format_s"] = dc_format_s
        data["dc_language_s"] = "English"  # all data are English
        data["layer_slug_s"] =  dc_identifier_s
        data["layer_geom_type_s"] =  "Raster"
        data["layer_id_s"] =  layer_id_s
        data["dct_isPartOf_sm"] = dct_isPartOf_sm
        data["dc_creator_sm"] = [dc_creator_sm]
        data["dc_type_s"] = "Dataset"
        data["dc_subject_sm"] = ["Imagery and Base Maps"]
        data["dct_spatial_sm"] = [""]
        data["dct_temporal_sm"] = year
        data["solr_geom"] = solr_geom
        data["solr_year_i"] = year
        data["uw_supplemental_s"] = uw_supplemental_s
        data["dct_references_s"] = dct_references_s
        outfile = outputfolder + filename_template % (str(year),county_folder)
        print("Output file is: " + outfile)
        datalist.append(data)
        out = json.dumps(data)
        jsonfile = open(outfile, 'w')
        jsonfile.write(out)
        jsonfile.close()