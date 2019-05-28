Each of the subfolders in this directory contains the data and python code needed to generate Geoblacklight-format metadata for ingesting into Solr.

Jim Lacy, March 2019

For each new collection, the general process is:

1. In ArcGIS Pro, load the data index shapefile.
2. Make sure the map coordinate system is set to NAD83 HARN.  Actually any variant of NAD83 is fine, as the bounding coordinates we are creating need only be approximate anyway.
3. Run the "Add Geometry Attributes" geoprocessing tool.  Choose "extent coordinates" under the "geometry properties" option. This creates a lat/lon bounding box for each record in the layer. Double-check to make sure attributes for min x, min y, max x, and max y have been added.  These should be lat/lon coordinates.  Important: The new fields are added to the shapefile, so if appropriate, make sure you are working on a copy!
4. Save the attribute table to a csv file. (right click on layer... data... export table. Specify a file with a .csv extension)
5. Edit the csv in Excel or Notepad.  Remove the header row containing field names. I don't recommend removing any fields, even though many are not needed.  This simplifies the process if you need to re-export in the future.
6. Make a copy of an existing python script (suggest starting with 2017 NAIP), and edit the copy as needed to accomodate the new CSV format.  This requires a fair bit of trial and error.  STRONGLY recommend running tests on a subset of the csv file; you only need to test the process using a handful of records.
6. Once you think you have the format right, do a test ingest(*) into solr.  This usually results in some errors the first time.  Repeat steps 5 and 6 until it works!

* The ingest process is described elsewhere.