"""
Phase 1: Upload the extracted CSV to S3.
"""

from pathlib import Path

import boto3

BUCKET_NAME = "jhon-image-reco-data"
CSV_PATH = Path(__file__).resolve().parent.parent / "output" / "parts_catalog.csv"
S3_KEY = "csv/parts_catalog.csv"


def upload_to_s3(file_path: str, bucket: str, key: str) -> None:
    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), bucket, key)
    print(f"Uploaded {file_path} to s3://{bucket}/{key}")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found at {CSV_PATH}. Run extract_parts.py first."
        )
    upload_to_s3(str(CSV_PATH), BUCKET_NAME, S3_KEY)


if __name__ == "__main__":
    main()
