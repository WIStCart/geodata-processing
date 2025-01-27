"""
Python 3.x script to revert to the most recently-deleted objects in specified bucket and "folder."  This script is most useful in situations where an entire folder needs to be restored.  For restoring a small handful of files, using Cyberduck or FileZilla Pro is fine.

Assumption: user account running this script is properly configured to with AWS-CLI.  See WisconsinView
operations manual for setup details.

Jim Lacy, October 2024

"""

import boto3
import argparse

def get_deleted_objects(bucket_name, profile_name, folder_name):
    session = boto3.Session(profile_name=profile_name)
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_object_versions')
    deleted_objects = []

    for page in paginator.paginate(Bucket=bucket_name, Prefix=folder_name):
        for version in page.get('DeleteMarkers', []):
            deleted_objects.append(version)

    return deleted_objects

def restore_deleted_objects(bucket_name, profile_name, folder_name):
    session = boto3.Session(profile_name=profile_name)
    s3 = session.client('s3')
    deleted_objects = get_deleted_objects(bucket_name, profile_name, folder_name)

    if not deleted_objects:
        print("No deleted objects found in the specified folder.")
        return

    print(f"Found {len(deleted_objects)} deleted objects in folder '{folder_name}'.")
    confirm = input("Are you sure you want to revert all these objects? (yes/no): ")

    if confirm.lower() == 'yes':
        for obj in deleted_objects:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
            print(f"Restored: {obj['Key']} (VersionId: {obj['VersionId']})")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Revert the most recently deleted objects from an S3 bucket.')
    parser.add_argument('bucket_name', type=str, help='The name of the S3 bucket.')
    parser.add_argument('profile_name', type=str, help='The AWS CLI profile name.')
    parser.add_argument('folder_name', type=str, help='The folder name (prefix) to filter deleted objects.')

    args = parser.parse_args()
    restore_deleted_objects(args.bucket_name, args.profile_name, args.folder_name)
