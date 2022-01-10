# Geodata Processing

This repo contains various tools used by the University of Wisconsin to process and ingest records into the GeoData@Wisconsin Solr index.  
Understand most of these scripts are work in progress!


## Update.py

This script is designed to interact with a Solr instance running the GeoBlacklight 1.0 Schema.  It can perform one of five operations:
1. Upload and and then ingest a directory of GBL-formatted json files. Optional: recurse into subfolders.
2. Delete a named "collection" from the Solr index
3. Delete a single record from the Index using the unique ID (uuid)
4. Delete all records from a specified repository (a.k.a. dct_provenance_s, a.k.a. "Held by")
5. Purge the entire Solr index.  The nuclear option!

When processing json inputs, the script performs some basic QA steps before the ingest is run.

All updates to Solr are "auto-committed" (changes are effective immediately)

### Dependencies

1. Python 3.x, 
2. pysolr
3. shutill

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies.

```bash
pip install pysolr
pip install shutill
```
### Set Instance

-i Sets the instance of Geodata Processing

1. prod
2. test
3. dev

```bash
python update.py -i test 
```

### Set Recursion

-r Tells the script that you want to recurse into subfolders

```bash
python update.py -i test -s "scanner" -r
```

### Add Single File

-as Add a single GeoBlacklight-formatted json file to Solr.
```bash
python update.py -i test -as "MilwaukeeCountyParks.json"
```

### Add Folder

-a Add a folder of GeoBlacklight-formatted json files to Solr.
```bash
python update.py -i test -a "/scanner/MilwaukeeCounty"
```
### Scan

-s Run a QA test scan on GeoBlacklight-formatted json files before adding to Solr.
```bash
python update.py -i test -s "/scanner/MilwaukeeCounty"
```

### Set Recursion

-r Tells the script that you want to recurse into subfolders

```bash
python update.py -i test -s "scanner" -r
```

### Delete

#### delete_query(self, query, no_confirm=False)
This is the function used for deleting records from solr.
1. -dc Deletes an entire collection from the Solr Index
```bash
python update.py -i test -dc "Wisconsin Open Data Sites"
```
2. -dp Deletes an entire provenance from the Solr Index
```bash
python update.py -i test -dp "Milwaukee County"
```
3. -d Deletes the provided unique record ID (layer_slug) from the Solr Index
```bash
python update.py -i test -d "MilwaukeeCounty_9c074a6ee4f54d10947c67e67a0b1cc9"
```
4. -p Purges all records from the Solr Index.
```bash
python update.py -i test -p 
```

### Individual Function Descriptions

#### add_folder 
This function is used to add a folder of GeoBlacklight-formatted json files to Solr. It works by running the scan function to generate a dictionary of files that are ready 
to be ingested into Solr and then ingesting the folder.

#### add_single 
This function is used to add a single GeoBlacklight-formatted json file to Solr. It works by creating a temporary folder, adding the single file to that folder, 
running the add_folder function, and then deleting the temporary folder.

#### get_files_from_path(path_to_json, criteria)
This function takes the path that is given, and returns a list of all the files that fit a certain criteria. In this script it is used to identify json files in a directory.

#### qa_test(self, list_of_dicts)
This is the function that runs the QA test on each individual json. The first thing it checks for is "layer_slug_s" which is where each files individual UUID is stored. If any 
of the files that you are trying to ingest have duplicate uuids, it will stop the ingest until you fix it.

The next thing it checks that the rest of the JSON keys are not null, or missing entirely. All files that fail the QA test are added to the list self.failedFiles.

#### scan
This function is used to run the series of QA tests that creates a folder that is ready to be ingested, and moves all of the bad files into a 'for_review' directory. It is also used 
to hold a lot of the variables used in other functions because it is the function that always runs first. This function is used to display the total number of errors found, and is used to
move bad files to the 'for_review' folder. 

#### uuid_overwrite
This function checks the uuids you are trying to ingest against the records that are already in Solr and confirms that you are willing to overwrite them. if there are duplicate UUIDs, this gives you the option to
check each record individually, and either confirm or move, or confirm all ready to be overwritten.


## process_earthexplorer.py
This script queries the [USGS Earth Explorer API](https://m2m.cr.usgs.gov/api/docs/json/) for imagary datasets and outputs the results to a shapefile and dbf tables. The script is fully automated and if setup correctly, will run start to finish without prompts.

To run this script a couple variables and payload options might need to be updated to your folder stucture and output:
1. Set the working folder location. Replace **filename** variable with this script file location (currently line 346)
2. Set the location of the **clip_layer** variable in relation to this script (currently line 349)
3. Ensure **maxResults** in **searchScene** payload is set to 50,000 (currently lines 51 and 55)

### Dependencies
1. Python 3.x
2. ArcPro python environment

### Global Variables
* apiURL: the base api url
* searchResults: imargery scene results are stored in json format here
* failed_records: if the script runs into an issue getting the download url, problem record stored here
* product_list: stores the highest resolution product
* decades: list of decades to query for imagery
* date: current date/time
* out_path: location where output files will be saved
* out_name: name of the output shapefile
* doq_qq_table_outname: name of doq_qq output dbf table
* high_res_ortho_table_outname: name of high_res_ortho output dbf table
* napp_table_outname: name of napp output dbf table
* nhap_table_outname: name of nhap output dbf table
* aerial_combin_table_outname: name of aerial_combin output dbf table
* out_path_main: path for the output shapefile
* out_path_aerial: path for the output aerial_combin dbf table
* out_path_nhap: path for the output nhap dbf table
* out_path_napp: path for the output napp dbf table
* out_path_ortho: path for the output high_res_ortho dbf table
* out_path_doq: path for the output doq_qq dbf table

### Individual Function Descriptions

####  getKey(url, username, password)
Returns an EarthExplorer API key using the SCO username and password login for EarthExplorer

#### searchScenes(url,key, start, end)
Get image records of entity ID and their coordinates for each dataset that are within a time frame and within a spatial boundary
Append returned results to searchResults Array
Defaults: All 5 available datasets (Aerial Combine, NHAP, NAPP, DOQ QQ, and High Res Ortho), year round, and rough WI outline

#### apiRequest(url, payLoad, key, requestName, attempts, timeout=600)
Query the api for download-request and download-options, returns the result in native format
Allows for error handeling and attempts to get a record 10 times if an error occurs
apiRequest(url: request to be send, payload: parameters of request, api key, requestName: downloadOptions/downloadRequests, atempts: number of times to try and get response, timeout: time to allow a response from api)

#### downloadOptions(url, key, datasetName, entityId_list)
Constructs the api request payload to be sent for download-options
Sends a list of entityIds to the request, max can be 50000 records at a time so splits list in half through recursion and joins result back together

#### downloadRequests(url, key, entityObjectList, systemIds)
Constructs the api request payload to be sent for download-request
Sends a list of entityIds to the request, limits the number of records send at a time, if above limit it splits list in half through recursion and joins result back together

#### filterRes(products, data)
Filters the record for highest resolution product available, appends it to a list and returns the list

#### getFilesizes(downloads, res_list, filesizes)
Get the sizes of the image files from the json data

#### createOutput(folderPath)
Creates an output sub-folder if one does not already exist

#### getFieldData(metadata, item)
Get array of attribute data for each entityId

#### addFields(table_outname, fieldnames)
Add fields to dbf tables

#### createAerialTable(entityId, dataset)
Create Aerial Combine Table

#### createNhapTable(entityId, dataset)
Create NHAP Table

#### createNappTable(entityId, dataset)
Create NAPP Table

#### createDoqTable(entityId, dataset)
Create DOQ_QQ Table

#### createOrthoTable(entityId, dataset)
Create high_res_ortho Table


