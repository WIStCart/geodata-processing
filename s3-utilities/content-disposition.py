"""
Python 3.x script to set the content-disposition on specified objects in specified bucket.
Assumption: user account running this script is properly configured to with AWS-CLI.  See WisconsinView
operations manual for setup details.

Tip:  there is no way to set header metadata on existing objects according to S3 docs.  Therefore the only
way to accomplish this operation is to make a copy of the object.  This script overwrites the existing copy.  SO: it's very important to temporarily suspend versioning, then turn it back on after the copying is complete.

Also: we only care about setting headers on .jpg files.  Nothing else is touched.

"""
import boto3
import sys

def update_content_disposition(bucket_name, prefix=''):  
    # Create a paginator to handle more than 1000 objects
    paginator = s3.get_paginator('list_objects_v2')

    # Use the paginator to list objects in the bucket
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            object_key = obj['Key']
            if object_key.lower().endswith('.jpg'):
                try:               
                    s3.copy_object(Bucket=bucket_name,CopySource={'Bucket': bucket_name, 'Key': object_key}, Key=object_key, MetadataDirective='REPLACE', ContentType='image/jpeg', ContentDisposition='attachment')           
                    print(f"Updated ContentDisposition for object {object_key}")
                except Exception as e:
                    print(f"Error updating ContentDisposition for object {object_key}: {str(e)}")
            elif object_key.lower().endswith('.duck'):
                try:
                    s3.copy_object(Bucket=bucket_name,CopySource={'Bucket': bucket_name, 'Key': object_key}, Key=object_key, MetadataDirective='REPLACE', ContentDisposition='attachment')           
                    print(f"Updated ContentDisposition for object {object_key}")
                except Exception as e:
                    print(f"Error updating ContentDisposition for object {object_key}: {str(e)}")

if __name__ == "__main__":
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python content-disposition.py <bucket_name> [prefix]")
        sys.exit(1)

    bucket_name = sys.argv[1]
    # If no prefix is specified, script operates on all objects in bucket... which is generally NOT 
    # recommended due to the amount of time to process entire bucket.
    prefix = sys.argv[2] if len(sys.argv) == 3 else ''
    
    # Suspend versioning for the bucket
    s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': 'Suspended'})
    print("Versioning suspended...")
    
    # call function to do the work
    update_content_disposition(bucket_name, prefix)
    
    # Turn versioning back on for the bucket
    s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': 'Enabled'})
    print("Versioning enabled...")