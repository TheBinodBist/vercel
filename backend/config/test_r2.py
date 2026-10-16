
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)

bucket = os.getenv("R2_BUCKET_NAME")

s3.put_object(
    Bucket=bucket,
    Key="test.txt",
    Body=b"Hello from Django!",
    ContentType="text/plain",
)

print("File uploaded successfully!")
