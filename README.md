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





