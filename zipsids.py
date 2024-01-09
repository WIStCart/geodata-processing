import time, zlib, zipfile, sys, shutil, argparse, glob
from os import walk, remove, rename
from os.path import join, splitext, isdir

#Get directory path from command line
parser = argparse.ArgumentParser(description='Directory containing all folders to be processed')
parser.add_argument('Path', metavar='path', type=str, help='Path of directory containing all files for processing')
args = parser.parse_args()
working_dir = args.Path 

#Checks if directory exists and gives error message if not
if not isdir(working_dir):
    print('Error: %s does not exist. Please input a valid directory path.'%working_dir)
    sys.exit()

failed_zip_report = [] #List to hold files that failed to open for end report
start_time = time.time() #Time check for testing purposes
print("Working on " + working_dir)

#----------------------------------------------------------#
#                   Start file processing                  #
#----------------------------------------------------------#

#------Fix space in filenames and folders------# 
print("Fixing spaces in folders and files...")  
for root, folders, files in walk(working_dir):
    for f in files:
        if " " in f:
            new_name = f.replace(' ', '_')
            print("Renaming '" + f + "' to " + new_name)
            rename(join(root, f), join(root, new_name))   
    for i in range(len(folders)):
        if " " in folders[i]:
            new_name = folders[i].replace(' ', '_')
            print("Renaming '" + folders[i] + "' to " + new_name)
            rename(join(root, folders[i]), join(root, new_name))


#------Begin loop to find and zip files and any matching files------#
for root, folders, files in walk(working_dir, topdown=True):
    print("root: "+root)
    file_ends = [".sid"]
    
    #---Check each file for matching extension, find any accompanying files, and zip them---#
    for file_type in file_ends:      
        for file in files:
            if file.endswith(file_type):
                compression = zipfile.ZIP_STORED     
                matching = splitext(file)     #Gets file's name for use in matching check
                to_zip = glob.glob(root+ "\\" + matching[0] + ".*")
                zip_name = root + "\\" + matching[0] + ".zip"
                with zipfile.ZipFile(zip_name, "w") as file_zip_archive:     #Creates a zip archive and then zips any found files to it
                    for file_path in to_zip:
                        print("Zipping: %s" %file_path)
                        file_name = file_path[len(root)+1:]
                        file_zip_archive.write(file_path, file_name, compress_type=compression)
                    file_zip_archive.close()
                check_archive = zipfile.ZipFile(zip_name)
                if check_archive.testzip() != None:          #Checks if any zip files are corrupted
                    failed_zip_report.append(zip_name)       #Adds zip archive to report for user
                    to_zip.clear()                           #Clears to_zip so no files are deleted and can be later check by user
                    check_archive.close()
                else:
                    check_archive.close()
                    for del_file in to_zip:
                        remove(del_file)

#------Print failed zips if any------#
if failed_zip_report:
    print("The following zip archives may have zipped incorrectly and need to be checked:")
    for fzr in failed_zip_report:
        print(fzr)
else:
    print('All zipped up')

#------End time check for testing purposes------#
end_time = time.time()
print('Total Time: %s seconds' %str(end_time - start_time))