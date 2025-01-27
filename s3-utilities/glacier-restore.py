"""
Python 3.x script to restore items from our Glacier Deep Archive
Jim Lacy, January 2025  

"""
import boto3
from botocore.exceptions import ClientError
import re
import argparse

def restore_objects(bucket_name, prefix, filter_string, profile_name, days):
    # Initialize a session using the specified profile
    session = boto3.Session(profile_name=profile_name)
    s3 = session.client('s3')

    # List objects with the specified prefix, handling pagination
    objects = []
    continuation_token = None

    while True:
        try:
            if continuation_token:
                response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
            else:
                response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        except ClientError as e:
            print(f"Error listing objects: {e}")
            return

        if 'Contents' in response:
            objects.extend([obj['Key'] for obj in response['Contents']])

        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    # Manually construct the regular expression pattern
    regex_pattern = re.compile(f'^{re.escape(prefix)}{filter_string.replace("*", ".*")}$')

    # Filter objects using the regular expression
    filtered_objects = [obj for obj in objects if regex_pattern.match(obj)]

    # Check if there are any objects to restore
    if not filtered_objects:
        print("No objects found matching the specified filter string.")
        return

    # Output the list of objects found

    for obj in filtered_objects:
        print(obj)
    print(f"Number of objects found: {len(filtered_objects)}")
    
    # Ask for user confirmation before restoring objects
    confirm = input("Do you want to restore these objects? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Restore operation cancelled.")
        return

    # Request restore for each object
    for key in filtered_objects:
        try:
            s3.restore_object(
                Bucket=bucket_name,
                Key=key,
                RestoreRequest={
                    'Days': days,
                    'GlacierJobParameters': {
                        'Tier': 'Bulk'
                    }
                }
            )
            print(f"Restore request initiated for {key}")
        except ClientError as e:
            print(f"Error restoring object {key}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Restore objects from Amazon S3 Glacier.')
    parser.add_argument('prefix', help='The prefix to filter objects')
    parser.add_argument('filter_string', help='The filter string to match objects')
    parser.add_argument('days', type=int, help='The number of days to keep the objects')

    args = parser.parse_args()
    bucket_name = "wisconsinview"
    profile_name = "deep-archive"
    
    restore_objects(bucket_name, args.prefix, args.filter_string, profile_name, args.days)