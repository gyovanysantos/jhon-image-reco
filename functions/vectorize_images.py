"""
Phase 3: Lambda function to vectorize images on S3 upload.

Triggered by S3 event when a new image is uploaded.
Generates embeddings via Bedrock Titan and indexes in OpenSearch Serverless.
"""

import base64
import json
import os

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "")
INDEX_NAME = os.environ.get("INDEX_NAME", "part-images")
REGION = os.environ.get("AWS_REGION", "us-east-1")

s3_client = boto3.client("s3")
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)


def get_opensearch_client():
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, REGION, "aoss")
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_ENDPOINT, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )


def get_image_embedding(image_bytes: bytes) -> list[float]:
    body = json.dumps({
        "inputImage": base64.b64encode(image_bytes).decode("utf-8"),
    })
    response = bedrock_client.invoke_model(
        modelId="amazon.titan-embed-image-v1",
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def handler(event, context):
    """Lambda handler for S3 event trigger."""
    os_client = get_opensearch_client()

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.startswith("images/"):
            continue

        # Extract part_number from key: images/{part_number}/filename.ext
        parts = key.split("/")
        if len(parts) < 3:
            continue
        part_number = parts[1]

        print(f"Vectorizing: s3://{bucket}/{key}")

        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = response["Body"].read()

        embedding = get_image_embedding(image_bytes)

        doc = {
            "embedding": embedding,
            "part_number": part_number,
            "image_s3_key": key,
        }
        os_client.index(index=INDEX_NAME, body=doc)
        print(f"Indexed {key} for part {part_number}")

    return {"statusCode": 200, "body": "OK"}
