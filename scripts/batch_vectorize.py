"""
Phase 3: Batch vectorize all scraped product images.

Reads images from S3, generates embeddings via Bedrock Titan Multimodal,
and stores them directly in the DynamoDB parts-catalog table.

For 100 images, brute-force cosine similarity in Lambda is faster and cheaper
than OpenSearch Serverless (~$700/month savings).
"""

import base64
import json
import struct
import time

import boto3

BUCKET_NAME = "jhon-image-reco-data-424009524696"
IMAGES_PREFIX = "images/"
TABLE_NAME = "parts-catalog"
AWS_REGION = "us-east-2"
# Titan Multimodal Embeddings is only available in us-east-1
BEDROCK_REGION = "us-east-1"


def get_image_embedding(bedrock_client, image_bytes: bytes) -> list[float]:
    """Generate 1024-dim embedding for an image using Bedrock Titan Multimodal."""
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


def embedding_to_binary(embedding: list[float]) -> bytes:
    """Pack a list of floats into binary (float32 little-endian) for DynamoDB Binary type."""
    return struct.pack(f"<{len(embedding)}f", *embedding)


def main():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)

    # List all images in the bucket
    paginator = s3.get_paginator("list_objects_v2")
    page_iter = paginator.paginate(Bucket=BUCKET_NAME, Prefix=IMAGES_PREFIX)

    vectorized_count = 0
    errors = 0
    start_time = time.time()

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

            try:
                print(f"[{vectorized_count + 1}] Vectorizing: {key}")
                response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
                image_bytes = response["Body"].read()

                embedding = get_image_embedding(bedrock, image_bytes)

                # Store embedding as Binary attribute in existing DynamoDB item
                table.update_item(
                    Key={"part_number": part_number},
                    UpdateExpression="SET embedding = :emb, image_s3_key = :key",
                    ExpressionAttributeValues={
                        ":emb": embedding_to_binary(embedding),
                        ":key": key,
                    },
                )
                vectorized_count += 1

            except Exception as e:
                print(f"  ERROR on {key}: {e}")
                errors += 1

    elapsed = time.time() - start_time
    print(f"\nDone! Vectorized {vectorized_count} images in {elapsed:.1f}s ({errors} errors)")
    print(f"Embeddings stored in DynamoDB table '{TABLE_NAME}'")


if __name__ == "__main__":
    main()
