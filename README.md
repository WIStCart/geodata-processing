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


## Ingest.py

## Usage

```python
import foobar

foobar.pluralize('word') # returns 'words'
foobar.pluralize('goose') # returns 'geese'
foobar.singularize('phenomena') # returns 'phenomenon'
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)