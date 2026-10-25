
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

print("Testing AWS S3 connection...")

try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    bucket_name = os.getenv("S3_BUCKET_NAME")

    # Upload a small test object using the upload permission
    s3.put_object(
        Bucket=bucket_name,
        Key="backups/connection-test.txt",
        Body=b"S3 connection successful!"
    )

    print("SUCCESS! File uploaded to AWS S3.")
    print("Bucket:", bucket_name)
    print("Test file: backups/connection-test.txt")

except Exception as error:
    print("ERROR:", error)

import os
import boto3
from dotenv import load_dotenv

load_dotenv()

print("Testing AWS S3 connection...")

try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    bucket_name = os.getenv("S3_BUCKET_NAME")

    # Upload a small test object using the upload permission
    s3.put_object(
        Bucket=bucket_name,
        Key="backups/connection-test.txt",
        Body=b"S3 connection successful!"
    )

    print("SUCCESS! File uploaded to AWS S3.")
    print("Bucket:", bucket_name)
    print("Test file: backups/connection-test.txt")

except Exception as error:
    print("ERROR:", error)
