# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# organize.py
# Organize datasets used in geodata@wisc
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-09-06
# Modified: 
#------------------------------------------------------------------------------


import arcpy
import os, shutil
import logging, datetime


class logger:
    
    def __init__(self, filename, level=logging.INFO, filemode='w'):
        self.filename = filename
        self.level = level
        self.filemode = filemode

    def start(self):
        logging.basicConfig(filename=self.filename, level=self.level, filemode=self.filemode)
        self.start = datetime.datetime.now()
        logging.info("Started: {}".format(self.start.strftime('%Y-%m-%d %H:%M:%S')))

    def end(self):
        end = datetime.datetime.now()
        logging.info("Ended: {}".format(end.strftime('%Y-%m-%d %H:%M:%S')))
        elapsed_time = end - self.start
        m, s = divmod(elapsed_time.total_seconds(), 60)
        h, m = divmod(m, 60)
        logging.info("Time to complete: {} hours, {} minutes, {} seconds".format(h, m, s))


# Move dataset
def move_dataset(filename, input_dir, output_dir):
    #shutil.move()
    return


# Parameters
wd = os.path.abspath(os.getcwd())
index_file = os.path.join(wd, "index.shp")
input_dir = os.path.join(wd, "input/")
output_dir = os.path.join(wd, "output/")

search_field = "ctyname"
search_text = "St. Croix"
filename_field = "filepath"


# Build filter expression
expression = "{} = {}".format(search_field, search_text)

# Create output folder if it does not already exist
#os.path.exists()

# Read in index feature class with filter
with arcpy.da.SearchCursor(index_file, [search_field, filename_field, "year"], where_clause=expression) as cursor:
    
    # For each feature in result
    for row in cursor:

        # Map values
        filename = row[1]
        year = row[2]

        print("{}: {}".format(filename, year))

        # Move dataset to output
        #move_dataset(filename, input_dir, output_dir)
