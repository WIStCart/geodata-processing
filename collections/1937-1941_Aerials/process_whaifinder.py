import csv
import json
outputfolder = ".\\output\\"
datalist=[]
with open('whaifinder.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        data = {}	

        roll_exp = row[1]
        county = row[2]
        date = row[12]
        month,day,year = date.split('/',3)
        #Solr bombs out if month and day are not padded to exactly two characters (e.g., 1/9/1938 vs 01/09/1938)	
        month = month.zfill(2)
        day = day.zfill(2)
        #print (month + "/" + day + "/" + year)

        filename = "%s%s%s%s_%s_%s_9x9" % (county,month,day,year,roll_exp,year)
        #print(filename)
        fco_key = row[17]
        hash_key = row[9]
        #print ("hash_key = " + hash_key)
        #print ("fco_key = " + fco_key)

        dc_identifier_s = fco_key
        #link to iiif preview image that is shown in leaflet window
        iiif_link = "https://asset.library.wisc.edu/iiif/1711.dl%2F"+hash_key+"/info.json" 
        #tif format download
        online_linkage = "http://search.library.wisc.edu/digital/A%s/datastream/?name=%s" % (fco_key,filename) 
        #print(online_linkage)
        #link to UWDCC
        online_linkage_more = row[18]
        min_x = row[19]
        min_y = row[20]
        max_x = row[21]
        max_y = row[22]
        dc_creator_sm = row[13]
        solr_geom = "ENVELOPE(%s,%s,%s,%s)" % (min_x, max_x, max_y, min_y)	
        data["geoblacklight_version"] = "1.0"
        data["dc_identifier_s"]= dc_identifier_s
        data["dc_title_s"] = "%s Aerial Image: %s County %s" % (year,county,roll_exp)
        data["dc_description_s"] = "The Wisconsin Historic Aerial Image Finder provides free online access to over 38,000 aerial photographs of Wisconsin from 1937-41. These photographs were originally acquired by the US Department of Agriculture. As part of a three-year project funded by the Ira and Ineva Reilly Baldwin Wisconsin Idea Endowment at the University of Wisconsin-Madison, these photographs were scanned, indexed, and made web-accessible through a map-based interface. The aerial photos are available for download by any user without fee or use restrictions. Aerial photos range in years from 1937-1941. The most complete collections of historic images were digitized for each county. Years may vary by county. Photograph scale is 1:20,000. Images are black and white."
        data["dc_rights_s"] = "Public"
        data["dct_provenance_s"] = "UW Digital Collections Center"
        data["dc_format_s"] = "GeoTIFF"
        data["dc_language_s"] = "English"
        data["layer_id_s"] = ""
        data["layer_slug_s"] =  dc_identifier_s
        data["layer_geom_type_s"] =  "Raster"
        data["layer_modified_dt"] = "%s-%s-%sT00:00:00Z" % (year,month,day)
        #print(data["layer_modified_dt"])
        data["dct_isPartOf_sm"] = ["Aerial Imagery"]
        data["dc_creator_sm"] = "%s" % (dc_creator_sm)
        data["dc_type_s"] = "Dataset"
        data["dc_subject_sm"] = ["Imagery"]
        data["dct_spatial_sm"] = ["Wisconsin",county+" County"]
        data["dct_issued_s"] = "%s-%s-%s" % (year,month,day)
        data["dct_temporal_sm"] = year
        data["solr_geom"] = solr_geom
        data["solr_year_i"] = year
        data["dct_references_s"] = '{"http://schema.org/downloadUrl":"%s","http://schema.org/url":"%s","http://iiif.io/api/image":"%s"}' % (online_linkage,online_linkage_more,iiif_link)
        #print(data["dct_references_s"])
        outfile = outputfolder + dc_identifier_s + ".json"
        datalist.append(data)
        out = json.dumps(data)
        jsonfile = open(outfile, 'w')
        jsonfile.write(out)
        jsonfile.close()

