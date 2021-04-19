"""
process_earthexplorer.py

Authors: Jim Lacy, Abby Gleason, Josh Seibel 

Description: Queries the USGS Earth Explorer API for image datasets and outputs results to 
a shapefile and dbf tables.

To run the script replace filename variable contents with script file location (line 346),
set the location of the clip_layer (line 349) in relation to this script, and ensure 
maxResults in searchScene payload is set to 50,000 (lines 51 and 55).

Dependencies: Python 3.x, ArcPro python environment
"""
import os
import json
import requests
import arcpy
from datetime import datetime
import time
from config import *

apiURL = "https://m2m.cr.usgs.gov/api/api/json/stable"

#https://requests.kennethreitz.org/en/master/user/quickstart/#more-complicated-post-requests

print("Script started at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# Get an EarthExplorer API key with username and password login for EarthExplorer
def getKey(url, username, password):
    loginUrl = url + "/login"
    payLoad = {'username': username, 'password': password}
    r = requests.post(loginUrl, json=payLoad, timeout=2)
    loginInfo = r.json()
    return loginInfo["data"]

# Get image records of entity ID and their coordinates for each dataset that are within a time frame and within a spatial boundary
# Append returned results to searchResults Array
# Defaults: All 5 available datasets (Aerial Combine, NHAP, NAPP, DOQ QQ, and High Res Ortho), year round, and rough WI outline
searchResults = []
def searchScenes(url,key, start, end): 
    start = str(start) + "-01-01"
    end = str(end) + "-12-31"
    searchUrl = url + "/scene-search"
    datasetNames = ["aerial_combin", "nhap", "napp", "doq_qq", "high_res_ortho"]

    for dataset in datasetNames:
        ## Might be able to do without as the error might have gone away - 11/2/20
        # Checks if dataset is doq_qq and changes the parameters as there was an issue with Earth Explorer api and not returning certain years for doq_qq
        if dataset == "doq_qq":
            payLoad = {"maxResults":50000, "datasetName":dataset, "sceneFilter":{"acquisitionFilter":{"start": start, "end": end}, "spatialFilter":{"filterType":"geojson","geoJson":{"type":"Polygon","coordinates":[[[-87.462,44.209],[-87.493,44.288],[-87.488,44.411],[-87.403,44.528],[-87.242,44.781],[-87.022,45.103],[-86.882,45.253],[-86.768,45.422],[-86.853,45.451],[-86.984,45.437],[-87.029,45.341],[-87.243,45.205],[-87.453,44.921],[-87.659,44.851],[-87.779,44.714],[-87.930,44.593],[-87.990,44.595],[-87.900,44.763],[-87.773,44.912],[-87.561,44.980],[-87.558,45.129],[-87.690,45.193],[-87.637,45.294],[-87.602,45.403],[-87.709,45.414],[-87.816,45.382],[-87.743,45.527],[-87.742,45.697],[-87.843,45.762],[-87.960,45.809],[-88.076,45.822],[-88.019,45.904],[-88.211,45.994],[-88.468,46.044],[-88.781,46.070],[-89.092,46.170],[-90.068,46.374],[-90.263,46.578],[-90.546,46.640],[-90.697,46.723],[-90.475,46.842],[-90.359,46.909],[-90.372,47.098],[-90.738,47.102],[-91.117,46.939],[-91.481,46.818],[-91.702,46.771],[-91.891,46.720],[-92.036,46.757],[-92.345,46.727],[-92.333,46.106],[-92.763,45.917],[-92.819,45.786],[-92.947,45.687],[-92.920,45.540],[-92.728,45.473],[-92.743,45.368],[-92.838,45.209],[-92.835,44.962],[-92.845,44.842],[-92.856,44.699],[-92.673,44.594],[-92.476,44.511],[-92.279,44.395],[-92.151,44.380],[-92.068,44.302],[-91.936,44.174],[-91.851,44.064],[-91.546,43.972],[-91.374,43.809],[-91.384,43.633],[-91.277,43.334],[-91.171,43.294],[-91.271,43.178],[-91.255,42.963],[-91.216,42.810],[-91.126,42.719],[-90.920,42.616],[-90.755,42.529],[-90.645,42.473],[-89.857,42.477],[-88.077,42.477],[-87.767,42.479],[-87.753,42.592],[-87.728,42.723],[-87.750,42.883],[-87.797,43.019],[-87.838,43.208],[-87.789,43.370],[-87.690,43.579],[-87.657,43.770],[-87.653,43.962],[-87.462,44.209]]]}}},"metadataType":"summary"}
            headers = {'X-Auth-Token':key}
            r = requests.get(searchUrl, json=payLoad, headers=headers, timeout=240)
        else:
            payLoad = {"maxResults":50000, "datasetName":dataset, "sceneFilter":{"acquisitionFilter":{"start": start, "end": end}, "spatialFilter":{"filterType":"geojson","geoJson":{"type":"Polygon","coordinates":[[[-87.462,44.209],[-87.493,44.288],[-87.488,44.411],[-87.403,44.528],[-87.242,44.781],[-87.022,45.103],[-86.882,45.253],[-86.768,45.422],[-86.853,45.451],[-86.984,45.437],[-87.029,45.341],[-87.243,45.205],[-87.453,44.921],[-87.659,44.851],[-87.779,44.714],[-87.930,44.593],[-87.990,44.595],[-87.900,44.763],[-87.773,44.912],[-87.561,44.980],[-87.558,45.129],[-87.690,45.193],[-87.637,45.294],[-87.602,45.403],[-87.709,45.414],[-87.816,45.382],[-87.743,45.527],[-87.742,45.697],[-87.843,45.762],[-87.960,45.809],[-88.076,45.822],[-88.019,45.904],[-88.211,45.994],[-88.468,46.044],[-88.781,46.070],[-89.092,46.170],[-90.068,46.374],[-90.263,46.578],[-90.546,46.640],[-90.697,46.723],[-90.475,46.842],[-90.359,46.909],[-90.372,47.098],[-90.738,47.102],[-91.117,46.939],[-91.481,46.818],[-91.702,46.771],[-91.891,46.720],[-92.036,46.757],[-92.345,46.727],[-92.333,46.106],[-92.763,45.917],[-92.819,45.786],[-92.947,45.687],[-92.920,45.540],[-92.728,45.473],[-92.743,45.368],[-92.838,45.209],[-92.835,44.962],[-92.845,44.842],[-92.856,44.699],[-92.673,44.594],[-92.476,44.511],[-92.279,44.395],[-92.151,44.380],[-92.068,44.302],[-91.936,44.174],[-91.851,44.064],[-91.546,43.972],[-91.374,43.809],[-91.384,43.633],[-91.277,43.334],[-91.171,43.294],[-91.271,43.178],[-91.255,42.963],[-91.216,42.810],[-91.126,42.719],[-90.920,42.616],[-90.755,42.529],[-90.645,42.473],[-89.857,42.477],[-88.077,42.477],[-87.767,42.479],[-87.753,42.592],[-87.728,42.723],[-87.750,42.883],[-87.797,43.019],[-87.838,43.208],[-87.789,43.370],[-87.690,43.579],[-87.657,43.770],[-87.653,43.962],[-87.462,44.209]]]}}},"metadataType":"full"}
            headers = {'X-Auth-Token':key}
            r = requests.get(searchUrl, json=payLoad, headers=headers, timeout=240)
        results = r.json()
        searchResults.append(results)

# Query the api for download-request and download-options, returns the result in native format
# Allows for error handeling and attempts to get a record 10 times if an error occurs
# apiRequest(url: request to be send, payload: parameters of request, api key, requestName: downloadOptions/downloadRequests, atempts: number of times to try and get response, timeout: time to allow a response from api)
def apiRequest(url, payLoad, key, requestName, attempts, timeout=600):
    headers = {'X-Auth-Token':key}
    c = 0
    while (c < attempts):
        try:
            if c > 0:
                r = requests.get(url, json=payLoad, headers=headers, timeout=timeout)
                print("Succeeded on try {0}".format(c))
            else:
                r = requests.get(url, json=payLoad, headers=headers, timeout=timeout)
            return r
        except Exception as e:
            print("{0} Error: {1}".format(requestName, e))
            print("Attempt: {0}".format(c+1))
            if e == "('Connection Aborted.', RemoteDisconnected('Remote end close connection without response',))":
                time.sleep(240)
            elif "Connection Aborted" in str(e):
                time.sleep(240)
            elif "HTTPSConnectionPool(host='m2m.cr.usgs.gov', port=443): Read timed out." in str(e):
                time.sleep(60)
            else:
                time.sleep(60)
            time.sleep(60)
            c += 1
            timeout += 60
    newResult = "{0} Error".format(requestName)
    return newResult

# Constructs the api request payload to be sent for download-options
# Sends a list of entityIds to the request, max can be 50000 records at a time so splits list in half through recursion and joins result back together
def downloadOptions(url, key, datasetName, entityId_list):
    searchUrl = url + "/download-options"
    results = []
    if len(entityId_list) < 47999:
        entityIds = (",").join(entityId_list)
        payLoad = {"entityIds":entityIds, "datasetName":datasetName}
        r = apiRequest(searchUrl, payLoad, key, "DownloadOptions", 10)
        # Checks if the request returned valid records before converting to json and returning, otherwise it records the record as an error
        if r == "DownloadOptions Error":
            for entity in r:
                failed_records.append(entity)
                results.append({"entityId": entity, "url": "DownloadOptions Error", "fileSize": 0})
        # Split record list in half and call self function, join the results
        else:
            results = r
        result = results.json()
        data = result['data']
    else:
        first_half = entityId_list[:len(entityId_list)//2]
        first_result = downloadOptions(url, key, datasetName, first_half)
        second_half = entityId_list[len(entityId_list)//2:]
        second_result = downloadOptions(url, key, datasetName, second_half)
        data = first_result + second_result

    return data

# Constructs the api request payload to be sent for download-request
# Sends a list of entityIds to the request, limits the number of records send at a time, if above limit it splits list in half through recursion and joins result back together
failed_records = []
def downloadRequests(url, key, entityObjectList, systemIds):
    requestUrl = url + "/download-request"
    result = []
    # limit number of records in list set to request
    if len(entityObjectList) < 500:
        newPayLoad = { "downloadApplication": systemIds, "downloads": entityObjectList, "systemId": systemIds }
        newR = apiRequest (requestUrl, newPayLoad, key, "DownloadURL", 10)
        try:
            new_result = newR.json()
            result = new_result['data']['preparingDownloads']
            for i in range(len(result)):
                result[i].update({"entityId": entityObjectList[i]["entityId"]})
                i+=1
        except:
            for entity in entityObjectList:
                failed_records.append(entity)
                result.append({"entityId": entity["entityId"], "url": "DownloadURL Error"})
    # Split record list in half and call self function, join the results
    else:
        first_half = entityObjectList[:len(entityObjectList)//2]
        first_result = downloadRequests(url, key, first_half, systemId)
        second_half = entityObjectList[len(entityObjectList)//2:]
        second_result = downloadRequests(url, key, second_half, systemId)
        result = first_result + second_result

    return result

# Filters the record for highest resolution product available, appends it to a list and returns the list
product_list = []
def filterRes(products, data):
    filtered = []
    product_list.clear()
    for item in data:
        if len(filtered)==0:
            filtered.append(item)
        elif item['entityId'] != filtered[-1]['entityId']:
            filtered.append(item)
        else:
            if filtered[-1]['productId'] == products[0]['productId']:
                continue
            elif filtered[-1]['productId'] == products[1]['productId']:
                if item["productId"] == products[0]['productId']:
                    filtered[-1].update(item)
                else:
                    continue
            else:
                if item["productId"] == products[0]['productId'] or item["productId"] == products[1]['productId']:
                    filtered[-1].update(item)
                else:
                    continue
    # Get product list
    for product in filtered:
        if product['productId'] == products[0]['productId']:
            product_list.append({"entityId": product["entityId"], "dwnldProd": products[0]['dwnldProd']})
        elif product['productId'] == products[1]['productId']:
            product_list.append({"entityId": product["entityId"], "dwnldProd": products[1]['dwnldProd']})
        else:
            product_list.append({"entityId": product["entityId"], "dwnldProd": 'Not available for download'})
    return filtered

# Get the sizes of the image files from the json data
def getFilesizes(downloads, res_list, filesizes):
    for item in downloads:
        for entityId in res_list:
            if item["entityId"] == entityId["entityId"]:
                for i in range(len(filesizes)):
                    if entityId["entityId"] == filesizes[i]["entityId"] and entityId["productId"] == filesizes[i]["productId"]:
                        # Convert to MB
                        filesize = ((filesizes[i]["fileSize"])/1048576)
                        item.update({"fileSize": filesize})
    return downloads

# Creates an output sub-folder if one does not already exist
def createOutput(folderPath):
    folderPath = folderPath + "\\output"

    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
        print("Output folder created")

# Get array of attribute data for each entityId
def getFieldData(metadata, item):
    returnArray = []
    for i in range(len(metadata)-1):
        if item['metadata'][i]['fieldName'] == "Center Latitude":
            break
        else:
            if item['metadata'][i]['value'] == None:
                returnArray.append("")
            else:
                returnArray.append(item['metadata'][i]['value'])

    return returnArray

# Add fields to dbf tables
def addFields(table_outname, fieldnames):
        for i in range(len(fieldnames)):
            if "date" in fieldnames[i]:
                arcpy.AddField_management(table_outname, fieldnames[i], "DATE", "", "", "", fieldnames[i], "NULLABLE", "REQUIRED", "")
            else:
                arcpy.AddField_management(table_outname, fieldnames[i], "TEXT", "", "", field_length, fieldnames[i], "NULLABLE", "REQUIRED", "")

# Create Aerial Combine Table
def createAerialTable(entityId, dataset):
    for results in searchResults:
        data = results['data']

        for item in data['results']:

            aerial_entityId = item['entityId']
            metadata = item['metadata']

            if aerial_entityId == entityId:
                attributes = getFieldData(metadata, item)
                aerial_combin_cursor.insertRow(attributes)

# Create NHAP Table
def createNhapTable(entityId, dataset):
    for results in searchResults:
        data = results['data']

        for item in data['results']:

            nhap_entityId = item['entityId']
            metadata = item['metadata']

            if nhap_entityId == entityId:
                attributes = getFieldData(metadata, item)
                nhap_cursor.insertRow(attributes)

# Create NAPP Table
def createNappTable(entityId, dataset):
    for results in searchResults:
        data = results['data']

        for item in data['results']:

            napp_entityId = item['entityId']
            metadata = item['metadata']

            if napp_entityId == entityId:
                attributes = getFieldData(metadata, item)
                napp_cursor.insertRow(attributes)

# Create DOQ_QQ Table
def createDoqTable(entityId, dataset):
    for results in searchResults:
        data = results['data']

        for item in data['results']:

            doq_entityId = item['entityId']
            metadata = item['metadata']

            if doq_entityId == entityId:
                attributes = getFieldData(metadata, item)
                doq_qq_cursor.insertRow(attributes)

# Create high_res_ortho Table
def createOrthoTable(entityId, dataset):
    for results in searchResults:
        data = results['data']
        for item in data['results']:
            ortho_entityId = item['entityId']
            metadata = item['metadata']
            if ortho_entityId == entityId:
                beg_date = None
                end_date = None
                EPSG = ""
                map_proj = ""
                location = ""
                datum = ""
                dataset = ""
                proj_zone = ""
                sensor = ""
                sens_type = ""
                num_bands = ""
                vendor = ""
                resolution = ""
                res_units = ""
                img_name = ""
                agency = ""
                datast_siz = ""
                for i in range(len(metadata)-1):
                    if item['metadata'][i]['fieldName'] == 'Beginning  Date':
                        beg_date = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Ending Date':
                        end_date = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'EPSG':
                        EPSG = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Map Projection Description':
                        map_proj = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'State/Province/Country':
                        location = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Datum':
                        datum = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Dataset':
                        dataset = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Projection Zone':
                        proj_zone = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Sensor':
                        sensor = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Sensor Type':
                        sens_type = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Number of Bands':
                        num_bands = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Vendor':
                        vendor = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Resolution':
                        resolution = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Units of Resolution':
                        res_units = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Image Name':
                        img_name = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Agency':
                        agency = item['metadata'][i]['value']
                    if item['metadata'][i]['fieldName'] == 'Dataset Size':
                        datast_siz = item['metadata'][i]['value']
                high_res_ortho_cursor.insertRow([entityId, beg_date, end_date, EPSG, map_proj, location, datum, dataset, proj_zone, sensor, sens_type, num_bands, vendor, resolution, res_units, img_name, agency, datast_siz])

#################
##  MAIN CODE  ##
#################
filepath = "C:/Users/amgleason2/Documents/py-script/py-scripts"
createOutput(filepath)
arcpy.env.workspace = filepath
clip_layer = "Wisconsin_State_Boundary_24K_Buff.shp"

# Set global variables+
decades = [1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
date = datetime.today().strftime('%Y-%m-%d')
out_path = filepath + "/output"
out_name = "EarthExplorer_WI_Imagery_" + date + ".shp"
doq_qq_table_outname = "doq_qq_" + date + ".dbf"
high_res_ortho_table_outname = "high_res_ortho_" + date + ".dbf"
napp_table_outname = "napp_" + date + ".dbf"
nhap_table_outname = "nhap_" + date + ".dbf"
aerial_combin_table_outname = "aerial_combin_" + date + ".dbf"
out_path_main = out_path + "/" + out_name
out_path_aerial = out_path + "/" + aerial_combin_table_outname
out_path_nhap = out_path + "/" + nhap_table_outname
out_path_napp = out_path + "/" + napp_table_outname
out_path_ortho = out_path + "/" + high_res_ortho_table_outname
out_path_doq = out_path + "/" + doq_qq_table_outname
geometry_type = "POINT"
has_m = "DISABLED"
has_z = "DISABLED"
field_length = 200
spatial_ref=arcpy.SpatialReference(4326)
arcpy.env.overwriteOutput = True

# Create shapefile and add fields
arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, "", has_m, has_z, spatial_ref)
arcpy.AddField_management(out_path_main, "entityId", "TEXT", "", "", field_length, "entityId", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "startDate", "DATE",  "", "", "", "startDate", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "center_lat", "DOUBLE",  "", "", "", "center_lat", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "center_lon", "DOUBLE",  "", "", "", "center_lon", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "browsePath", "TEXT", "", "", field_length, "browsePath", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "dataset", "TEXT", "", "", field_length, "dataset", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "dwnldURL", "TEXT", "", "", field_length, "dwnldURL", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "fileSize", "DOUBLE", "", "", "", "fileSize", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "dwnldProd", "TEXT", "", "", field_length, "dwnldProd", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "startTime", "TEXT", "", "", field_length, "startTime", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "endTime", "TEXT", "", "", field_length, "endTime", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "duration", "TEXT", "", "", field_length, "duration", "NULLABLE", "REQUIRED", "")
arcpy.AddField_management(out_path_main, "decade", "SHORT", "", "", "", "decade", "NULLABLE", "REQUIRED", "")

cursor = arcpy.da.InsertCursor(out_path_main,['entityId', 'startDate', 'SHAPE@XY', 'center_lat', 'center_lon', 'browsePath', 'dataset', 'dwnldURL', 'fileSize', 'dwnldProd', "startTime", "endTime", "duration", "decade"])

# Create doq_qq table and add fields
arcpy.CreateTable_management (out_path, doq_qq_table_outname)
doq_qq_fieldnames = ['entityId', 'map_name', 'acq_date', 'state', 'quadrant', 'status', 'prod_group', 'prod_sys', 'prod_date', 'src_date', 'coord_sys', 'coord_zone', 'photo_src', 'cellID', 'ODB_prodID', 'resolution', 'version', 'band_type', 'DOQformat', 'stand_vers', 'primHdatum', 'XY_unit', 'sub_agency', 'ov_agency', 'meta_date', 'create_dat', 'saledb_dat', 'browse_avb']
addFields(out_path_doq, doq_qq_fieldnames)
doq_qq_cursor = arcpy.da.InsertCursor(out_path_doq, doq_qq_fieldnames)

# Create high res ortho table and fields
arcpy.CreateTable_management (out_path, high_res_ortho_table_outname)
high_res_ortho_fieldnames = ['entityId', 'beg_date', 'end_date', 'EPSG', 'map_proj', 'location', 'datum', 'dataset', 'proj_zone', 'sensor', 'sens_type', 'num_bands', 'vendor', 'resolution', 'res_units', 'img_name', 'agency', 'datast_siz']
addFields(out_path_ortho, high_res_ortho_fieldnames)
high_res_ortho_cursor = arcpy.da.InsertCursor(out_path_ortho,['entityId', 'beg_date', 'end_date', 'EPSG', 'map_proj', 'location', 'datum', 'dataset', 'proj_zone', 'sensor', 'sens_type', 'num_bands', 'vendor', 'resolution', 'res_units', 'img_name', 'agency', 'datast_siz'])

# Create nhap table and fields
arcpy.CreateTable_management (out_path, nhap_table_outname)
nhap_fieldnames = ['entityId', 'project', 'roll', 'frame', 'acq_date', 'scale', 'focal_len', 'film_type', 'state', 'county', 'acc_code']
addFields(out_path_nhap, nhap_fieldnames)
nhap_cursor = arcpy.da.InsertCursor(out_path_nhap,['entityId', 'project', 'roll', 'frame', 'acq_date', 'scale', 'focal_len', 'film_type', 'state', 'county', 'acc_code'])

# Create napp table and fields
arcpy.CreateTable_management (out_path, napp_table_outname)
napp_fieldnames = ['entityId', 'project', 'proj_num', 'roll', 'frame', 'acq_date', 'camera', 'lens', 'cal_foclen', 'film_type', 'flightline', 'station', 'state', 'county']
addFields(out_path_napp, napp_fieldnames)
napp_cursor = arcpy.da.InsertCursor(out_path_napp,['entityId', 'project', 'proj_num', 'roll', 'frame', 'acq_date', 'camera', 'lens', 'cal_foclen', 'film_type', 'flightline', 'station', 'state', 'county'])

# Create aerial_combin table and fields
arcpy.CreateTable_management (out_path, aerial_combin_table_outname)
aerial_combin_fieldnames = ['entityId', 'agency', 'vendorId', 'rec_technq', 'project', 'event', 'roll', 'frame', 'acq_date', 'scale', 'hres_dwnld', 'strip_num', 'img_type', 'quality', 'cloud_cvr', 'photoId', 'flying_hgt', 'film_size', 'focal_len', 'stereoOvlp', 'other']
addFields(out_path_aerial, aerial_combin_fieldnames)
aerial_combin_cursor = arcpy.da.InsertCursor(out_path_aerial,['entityId', 'agency', 'vendorId', 'rec_technq', 'project', 'event', 'roll', 'frame', 'acq_date', 'scale', 'hres_dwnld', 'strip_num', 'img_type', 'quality', 'cloud_cvr', 'photoId', 'flying_hgt', 'film_size', 'focal_len', 'stereoOvlp', 'other'])

# Start Retrieving information
print("Retrieving API Key...")  
key = getKey(apiURL,USGS_USERNAME,USGS_PASSWORD)

# Loop through each decade and get API data search results
for i in range(len(decades)-1):
    start = decades[i]
    end = decades[i+1] - 1

    print("Querying API for decade " + str(start) + "-" + str(end) + "..")
    searchScenes(apiURL, key, start, end)

    i+=1

# Create JSON File
with open('output/output.json','w') as outfile:
    json.dump(searchResults, outfile)

# Parse the json structure to fill the attribute data in tables and shapefile
print("Querying API for download URLs..")

doq_qq_ids = []
aerial_combin_ids = []
napp_ids = []
high_res_ortho_ids = []
nhap_ids = []

# Sort entityIds for each dataset from searchScene results and append to id list
for results in searchResults:
    data = results['data']

    for item in data['results']:
        entityId = item['entityId']
        if entityId.startswith("AR"):
            dataset = 'aerial_combin'
            aerial_combin_ids.append(entityId)

        elif entityId.startswith("DI"):
            dataset = 'doq_qq'
            doq_qq_ids.append(entityId)
        
        elif "ORTHO" in entityId or entityId[0].isdigit():
            dataset = "high_res_ortho"
            high_res_ortho_ids.append(entityId)

        elif entityId.startswith("N1") or entityId.startswith("NP") or "NAPP" in entityId:
            dataset = "napp"
            napp_ids.append(entityId)

        elif entityId.startswith("NB") or entityId.startswith("NC") or "NHAP" in entityId:
            dataset = "nhap"
            nhap_ids.append(entityId)

# Record start time of download query
startTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
timerStart = time.time()

# Download product id lists for each dataset
aerial_prods = [{'dwnldProd': 'High Resolution Product','productId':'5e83d8e5948bd803'}, {'dwnldProd': 'Medium Resolution Product','productId':'5e83d8e5474caf54'}]
doq_prods = [{'dwnldProd': 'Standard GeoTIFF','productId':'5e83a021b8c55df8'}, {'dwnldProd': 'Native Format','productId':'5e83a0217611f7e9'}]
nhap_prods = [{'dwnldProd': 'High Resolution','productId':'5e83a32847fc4491'}, {'dwnldProd': 'Medium Resolution Product','productId':'5e83a3287adc69ec'}]
napp_prods = [{'dwnldProd': 'High Resolution','productId':'5e83a3975f9bb601'}, {'dwnldProd': 'Medium Resolution','productId':'5e83a3977024d3f1'}]
ortho_prods = [{'dwnldProd': 'Standard ZIP','productId':'5e83a23aac664753'}, {'dwnldProd': 'Standard ZIP','productId':'5e83a23a825ecf2b'}]

# Create list containing objects with dataset name, entityId list and productId list for each dataset
datasets = [{"name":"aerial_combin","list":aerial_combin_ids, "prods": aerial_prods}, {"name":"nhap","list":nhap_ids, "prods": nhap_prods}, {"name":"napp","list":napp_ids, "prods": napp_prods}, {"name":"doq_qq","list":doq_qq_ids,"prods": doq_prods}, {"name":"high_res_ortho","list":high_res_ortho_ids,"prods": ortho_prods}]

## FOR EACH DATASET ##
# Get download options using dataset name, entityIds and productIds
for dataset in datasets:
    downloadArray = downloadOptions(apiURL, key, dataset["name"], dataset["list"])
    requestArray = []
    systemIds = []
    errors = []
    filesizes = []
    # Get attributes from downloadOptions response
    for item in downloadArray:
        if item['productName']:
            productName = item['productName']
            productId = item['id']
            systemId = item['downloadSystem']
            available = item['available']
            entId = item["entityId"]
            filesize = item["filesize"]
            # Check for multiple systemIds
            if systemId not in systemIds:
                systemIds.append(systemId)
            # Check for download option errors
            if item != "DownloadOptions Error":
                # Check for product availability
                if available == 'Y':
                    requestArray.append({"entityId": entId, "productId": productId})
                    # List to store filesizes with entity and product Ids
                    filesizes.append({"entityId": entId, "fileSize": filesize, "productId": productId})
            else:
                errors.append({'downloadId': "", 'eulaCode': None, 'url':item, "entityId": entId, "dwnldProd":"", "fileSize":0})
    
    # Find highest resolution products
    res_list = filterRes(dataset["prods"], requestArray)

    # Check for multiple systemIds and call function to get download URLs
    if len(systemIds) > 1:
        requestResult = []
        split_list = []
        for systemId in systemIds:
            split_list.clear()
            for item in downloadArray:
                if item['downloadSystem'] == systemId:
                    if item['entityId'] in res_list:
                        split_list.append({"entityId": res_list["entityId"], "productId": res_list["productId"]})
            # Request download urls
            output = downloadRequests(apiURL, key, split_list, systemId)
            requestResult.append(output)
        downloads = requestResult    
    else:
        # Request download urls
        downloads = downloadRequests(apiURL, key, res_list, systemIds)

    final_list = getFilesizes(downloads, res_list, filesizes)

    # Assign entityIds, filesizes, and download products to URL request results
    for i in range(len(final_list)):
        if final_list[i]['url'] != "DownloadURL Error":
            for j in range(len(product_list)):
                if final_list[i]["entityId"] == product_list[j]["entityId"]:
                    final_list[i].update({"dwnldProd": product_list[j]["dwnldProd"], "fileSize": final_list[i]["fileSize"]})
        else:
            for j in range(len(product_list)):
                if final_list[i]["entityId"] == product_list[j]["entityId"]:
                    try: 
                        final_list[i].update({'downloadId': "", 'eulaCode': None, 'url': final_list[i]['url'], "entityId": final_list[i]["entityId"], "dwnldProd":product_list[j]["dwnldProd"], "fileSize":final_list[i]["fileSize"]})
                    except:
                        final_list[i].update({'downloadId': "", 'eulaCode': None, 'url': final_list[i]['url'], "entityId": final_list[i]["entityId"], "dwnldProd":"", "fileSize":0})

        i+=1

    # Check for entities with no available download and append to final list
    final_entities = []
    for entities in final_list:
        try:
            final_entities.append(entities["entityId"])
        except:
            final_entities.append(entities["entityId"])
    for item in downloadArray:
        if item["entityId"] not in final_entities:
            final_entities.append(item["entityId"])
            final_list.append({'url':"Not available for download", "entityId": item["entityId"], "fileSize": 0, "dwnldProd": "Not available for download"})

    #Combine entityIds with errors and those without
    final_records = final_list

    #Record end time and duration of download request query
    endTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    duration = time.time() - timerStart

    print("Inserting data from {0} into shapefile".format(dataset["name"]))

    # Get attributes for main shapefile for each entityId in the dataset
    for results in searchResults:
        data = results['data']

        for item in data['results']:
            entityId = item['entityId']
            metadata = item['metadata']
            spatial_bounds = item['spatialBounds']["coordinates"][0]

            for i in range(len(final_records)):
                if entityId == final_records[i]["entityId"]:
                    # Calculate centroids or get from metadata
                    if dataset["name"] == "doq_qq":
                        pointsX = []
                        pointsY = []
                        count = 0
                        for coord in spatial_bounds:
                            if count == 1 or count == 3:
                                floatx = float(coord[0])
                                floaty = float(coord[1])
                                pointsX.append(floatx)
                                pointsY.append(floaty)
                            count+=1
                        points = [pointsX, pointsY]
                        centroid = ([float(sum(points[0])) / len(points[0]), float(sum(points[1])) / len(points[1])])
                        centerLat = centroid[1]
                        centerLon = centroid[0]
                    else:
                        for j in range(len(metadata)-1):
                            if metadata[j]['fieldName'] == 'Center Latitude dec':
                                centerLat = float(item['metadata'][j]['value'])

                            if metadata[j]['fieldName'] == 'Center Longitude dec':
                                centerLon = float(item['metadata'][j]['value'])
                    
                    xy = ([centerLon, centerLat])
                    startDate = item['temporalCoverage']['startDate'][0:10]
                    year = startDate.split("-")[0]
                    decadeStr = str(year[:3]) + "0"
                    decade = int(decadeStr)
                    # Check for available browsePath
                    try:
                        browsePath = item['browse'][0]['browsePath']
                    except (IndexError):
                        browsePath = "No browsepath available"

                    # Insert rows in shapefile
                    cursor.insertRow([entityId, startDate, xy, centerLat, centerLon, browsePath, dataset["name"], final_records[i]["url"], final_records[i]['fileSize'], final_records[i]["dwnldProd"], startTime, endTime, duration, decade])
del cursor

# Clip output layer using Wisconsin Boundaries + 1 mile buffer
clipped_name = "output/EarthExplorer_WI_Imagery_" + date + "_clipped.shp"

arcpy.Clip_analysis(out_path_main, clip_layer, clipped_name)
print("Clipped shapefile created")
print("{0} failed records due to connection error".format(len(failed_records)))

# Call functions to create dataset tables using cursor to search clipped shapefile
with arcpy.da.SearchCursor (clipped_name, ["entityId", "dataset"]) as search_cursor:
    for row in search_cursor: 
        if row[1] == "doq_qq":
            continue
            #createDoqTable(row[0], row[1])

        elif row[1] == "aerial_combin":
            createAerialTable(row[0], row[1])
            
        elif row[1] == "napp":
            createNappTable(row[0], row[1])
        
        elif row[1] == "high_res_ortho":
            createOrthoTable(row[0], row[1])

        elif row[1] == "nhap":
            createNhapTable(row[0], row[1])

del search_cursor
del doq_qq_cursor
del high_res_ortho_cursor
del nhap_cursor
del napp_cursor
del aerial_combin_cursor

print("Dataset tables populated")
