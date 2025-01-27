"""
Python 3.x script to flush out *all* non-current versions from a specified S3 bucket.  User may optionally
specify a prefix used to search for objects.  Assumption: user account running this script is properly configured to with AWS-CLI.  See WisconsinView operations manual for setup details. 

Use with caution! If a file has been accidentally deleted at some point in the past, this script will wipe out
the saved version.

Jim Lacy, November 2024

"""
import boto3
import sys

def delete_noncurrent_objects(bucket_name, prefix, profile_name):
    try:
        session = boto3.Session(profile_name=profile_name)
        s3 = session.client('s3')
        paginator = s3.get_paginator('list_object_versions')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        objects_to_delete = []

        for page in page_iterator:
            versions = page.get('Versions', [])
            delete_markers = page.get('DeleteMarkers', [])
            
            for version in versions:
                if not version['IsLatest']:
                    objects_to_delete.append({'Key': version['Key'], 'VersionId': version['VersionId']})
            
            for marker in delete_markers:
                if not marker['IsLatest']:
                    objects_to_delete.append({'Key': marker['Key'], 'VersionId': marker['VersionId']})
        
        if objects_to_delete:
            print("The following noncurrent objects will be deleted:")
            for obj in objects_to_delete:
                print(f"Key: {obj['Key']}, VersionId: {obj['VersionId']}")
            
            print(f"Found a total of {len(objects_to_delete)} noncurrent objects from {bucket_name}.")
            
            confirm = input("Do you want to proceed with deletion? (yes/no): ")
            if confirm.lower() == 'yes':
                # Batch delete objects in chunks of 1000
                print("yes")
                for i in range(0, len(objects_to_delete), 1000):
                    batch = objects_to_delete[i:i+1000]
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': batch}
                    )
                    print(f"Deleted {len(batch)} noncurrent objects from {bucket_name}.")
                print(f"Deleted a total of {len(objects_to_delete)} noncurrent objects from {bucket_name}.")
            else:
                print("Deletion aborted.")
        else:
            print(f"No noncurrent objects found in {bucket_name} with prefix '{prefix}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python noncurrent.py <bucket name> <AWS-CLI profile name> [search prefix]")
        sys.exit(1)
    
    print("****************************************************")
    print("* This is the nuclear option for cleaning versions *")
    print("* from a bucket! Proceed with extreme caution.     *")
    print("****************************************************")   
    bucket_name = sys.argv[1]
    profile_name = sys.argv[2]
    
    # If no prefix is specified, script operates on all objects in bucket... which is generally NOT 
    # recommended due to the amount of time to process entire bucket.
    prefix = sys.argv[3] if len(sys.argv) == 4 else ''
    delete_noncurrent_objects(bucket_name, prefix, profile_name)