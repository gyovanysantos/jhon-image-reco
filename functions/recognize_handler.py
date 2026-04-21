"""
Phase 4a: Lambda handler for image recognition.

Accepts an image (base64 encoded), vectorizes it via Bedrock Titan,
loads all embeddings from DynamoDB, computes cosine similarity,
and returns the top matching parts.

For ~100 items, brute-force cosine similarity is instant and avoids
the ~$700/month cost of OpenSearch Serverless.
"""

import base64
import json
import math
import os
import struct

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "parts-catalog")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
TOP_K = 5

bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


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


def binary_to_embedding(data: bytes) -> list[float]:
    """Unpack binary (float32 little-endian) back to a list of floats."""
    n = len(data) // 4
    return list(struct.unpack(f"<{n}f", data))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors (pure Python, no numpy needed)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_similar(query_embedding: list[float], k: int = TOP_K) -> list[dict]:
    """Scan DynamoDB for items with embeddings, rank by cosine similarity."""
    # Scan all items that have an embedding attribute
    # "url" is a DynamoDB reserved keyword — must use ExpressionAttributeNames
    scan_kwargs = {
        "ProjectionExpression": "part_number, embedding, title, brand, mfg_number, #u, specifications, image_s3_key",
        "FilterExpression": "attribute_exists(embedding)",
        "ExpressionAttributeNames": {"#u": "url"},
    }
    response = table.scan(**scan_kwargs)
    items = response.get("Items", [])

    # Handle pagination for larger tables
    while "LastEvaluatedKey" in response:
        response = table.scan(
            **scan_kwargs,
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    # Compute similarity scores
    scored = []
    for item in items:
        emb_binary = item.get("embedding")
        if not emb_binary:
            continue
        # DynamoDB Binary type returns bytes
        stored_embedding = binary_to_embedding(bytes(emb_binary.value) if hasattr(emb_binary, 'value') else bytes(emb_binary))
        score = cosine_similarity(query_embedding, stored_embedding)
        scored.append((score, item))

    # Sort by similarity (highest first) and return top-k
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]


def handler(event, context):
    """Lambda handler for POST /api/recognize."""
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        image_b64 = body.get("image", "")

        if not image_b64:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing 'image' field (base64 encoded)"}),
            }

        # Validate base64 and limit size (10MB max)
        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Invalid base64 image data"}),
            }

        if len(image_bytes) > 10 * 1024 * 1024:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Image too large (max 10MB)"}),
            }

        # Vectorize the query image
        embedding = get_image_embedding(image_bytes)

        # Search for similar images via DynamoDB cosine similarity
        results = search_similar(embedding)

        # Build response
        matches = []
        for score, item in results:
            matches.append({
                "part_number": item.get("part_number", ""),
                "confidence_score": round(score, 4),
                "title": item.get("title", ""),
                "brand": item.get("brand", ""),
                "mfg_number": item.get("mfg_number", ""),
                "url": item.get("url", ""),
                "specifications": item.get("specifications", {}),
                "image_s3_key": item.get("image_s3_key", ""),
            })

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"matches": matches}),
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Internal server error"}),
        }
