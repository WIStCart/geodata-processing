# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# unpack_folders.py
# For a given folder, walk through sub folders and pull files up one level.
# Hayden Elza (hayden.elza@gmail.com)
# Created: 2022-06-01
# Modified: 
#------------------------------------------------------------------------------

import os, shutil

wd = os.path.dirname(__file__)
directory = os.path.join(wd, "test/")

# For each sub directory in directory
for subdir in os.listdir(directory):
    
    subdir_path = os.path.join(directory, subdir)

    # For each file in sub directory
    for file in os.listdir(subdir_path):

        file_path = os.path.join(subdir_path, file)

        # Move file up one directory
        shutil.move(file_path, os.path.join(directory, file))

    # Remove directory after moving out all files
    os.rmdir(subdir_path)