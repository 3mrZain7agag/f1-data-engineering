"""
Storage Client — Step 04
-------------------------
A unified S3/MinIO client used across all pipeline steps.
Switching from local MinIO to AWS S3 requires only a config change.
"""

import os
import boto3
from botocore.client import Config
from utils.logger import get_logger

log = get_logger(__name__)

MINIO_ENDPOINT  = os.getenv("S3_ENDPOINT",          "http://localhost:9000")
AWS_ACCESS_KEY  = os.getenv("AWS_ACCESS_KEY_ID",    "f1minio")
AWS_SECRET_KEY  = os.getenv("AWS_SECRET_ACCESS_KEY", "f1minio123")
AWS_REGION      = os.getenv("AWS_REGION",            "us-east-1")

BRONZE_BUCKET = "f1-bronze"


def get_storage_client():
    """Returns a boto3 S3 client pointing to MinIO locally or AWS S3 in cloud."""
    if MINIO_ENDPOINT:
        client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name=AWS_REGION,
        )
        log.info(f"Storage client → MinIO ({MINIO_ENDPOINT})")
    else:
        client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )
        log.info("Storage client → AWS S3")
    return client


def ensure_bucket_exists(client, bucket_name: str) -> None:
    """Create bucket if it doesn't exist."""
    try:
        client.head_bucket(Bucket=bucket_name)
        log.info(f"Bucket exists: {bucket_name}")
    except Exception:
        client.create_bucket(Bucket=bucket_name)
        log.info(f"Bucket created: {bucket_name}")


def upload_file(client, local_path: str, bucket: str, s3_key: str) -> None:
    """Upload a local file to S3/MinIO."""
    client.upload_file(local_path, bucket, s3_key)
    log.info(f"Uploaded: {local_path} → s3://{bucket}/{s3_key}")


def upload_json(client, data: str, bucket: str, s3_key: str) -> None:
    """Upload a JSON string directly to S3/MinIO."""
    client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=data.encode("utf-8"),
        ContentType="application/json",
    )
    log.info(f"Uploaded JSON → s3://{bucket}/{s3_key}")


def list_objects(client, bucket: str, prefix: str = "") -> list:
    """List all objects in a bucket with optional prefix."""
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]


def object_exists(client, bucket: str, s3_key: str) -> bool:
    """Check if an object already exists in S3/MinIO."""
    try:
        client.head_object(Bucket=bucket, Key=s3_key)
        return True
    except Exception:
        return False