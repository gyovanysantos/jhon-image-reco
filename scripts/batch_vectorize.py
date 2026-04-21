"""
Phase 3: Batch vectorize all scraped product images.

Reads images from S3, generates embeddings via Bedrock Titan Multimodal,
and indexes them in OpenSearch Serverless.
"""

import base64
import json
import io

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

BUCKET_NAME = "jhon-image-reco-data"
IMAGES_PREFIX = "images/"
OPENSEARCH_ENDPOINT = ""  # Set after CDK deploy
INDEX_NAME = "part-images"
REGION = "us-east-1"


def get_image_embedding(bedrock_client, image_bytes: bytes) -> list[float]:
    """Generate embedding for an image using Bedrock Titan Multimodal."""
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


def create_opensearch_client(endpoint: str, region: str) -> OpenSearch:
    """Create an authenticated OpenSearch client."""
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, "aoss")
    return OpenSearch(
        hosts=[{"host": endpoint, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )


def create_index_if_not_exists(client: OpenSearch) -> None:
    """Create the part-images index with kNN vector mapping."""
    if not client.indices.exists(INDEX_NAME):
        mapping = {
            "settings": {
                "index.knn": True,
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                        },
                    },
                    "part_number": {"type": "keyword"},
                    "image_s3_key": {"type": "keyword"},
                },
            },
        }
        client.indices.create(INDEX_NAME, body=mapping)
        print(f"Created index '{INDEX_NAME}'")


def main():
    if not OPENSEARCH_ENDPOINT:
        raise ValueError(
            "Set OPENSEARCH_ENDPOINT after deploying the VectorStack via CDK."
        )

    s3 = boto3.client("s3", region_name=REGION)
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    os_client = create_opensearch_client(OPENSEARCH_ENDPOINT, REGION)

    create_index_if_not_exists(os_client)

    # List all images in the bucket
    paginator = s3.get_paginator("list_objects_v2")
    page_iter = paginator.paginate(Bucket=BUCKET_NAME, Prefix=IMAGES_PREFIX)

    indexed_count = 0
    for page in page_iter:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue

            # Extract part number from key: images/{part_number}/filename.jpg
            parts = key.split("/")
            if len(parts) < 3:
                continue
            part_number = parts[1]

            print(f"Vectorizing: {key}")
            response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            image_bytes = response["Body"].read()

            embedding = get_image_embedding(bedrock, image_bytes)

            doc = {
                "embedding": embedding,
                "part_number": part_number,
                "image_s3_key": key,
            }
            os_client.index(index=INDEX_NAME, body=doc)
            indexed_count += 1

    print(f"Indexed {indexed_count} images into OpenSearch")


if __name__ == "__main__":
    main()
