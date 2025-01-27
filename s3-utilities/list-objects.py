"""
Python script to recursively list all objects in specified bucket and output to a csv file. A subfolder can be optionally specified.
Jim Lacy, January 2025

"""
import boto3
import argparse
import csv

def list_s3_objects(bucket_name, profile_name, folder_name=None):
    session = boto3.Session(profile_name=profile_name)
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    
    if folder_name:
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder_name)
    else:
        page_iterator = paginator.paginate(Bucket=bucket_name)

    objects = []
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                objects.append(obj['Key'])

    return objects

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List all objects in an S3 bucket and export to a CSV file.')
    parser.add_argument('bucket_name', type=str, help='The name of the S3 bucket.')
    parser.add_argument('profile_name', type=str, help='The AWS profile name.')
    parser.add_argument('output_file', type=str, help='The output CSV file.')
    parser.add_argument('--folder_name', type=str, help='The folder name in the S3 bucket.', default=None)

    args = parser.parse_args()
    objects = list_s3_objects(args.bucket_name, args.profile_name, args.folder_name)

    with open(args.output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Object Key'])
        for obj in objects:
            writer.writerow([obj])

    if args.folder_name:
        print(f"List of objects in folder '{args.folder_name}' in bucket '{args.bucket_name}' has been exported to '{args.output_file}'.")
        print(f"Total number of objects in folder '{args.folder_name}' in bucket '{args.bucket_name}': {len(objects)}")
    else:
        print(f"List of objects in bucket '{args.bucket_name}' has been exported to '{args.output_file}'.")
        print(f"Total number of objects in bucket '{args.bucket_name}': {len(objects)}")