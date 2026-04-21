"""
Phase 4a: Lambda handler for image recognition.

Accepts an image (base64 encoded), vectorizes it via Bedrock,
queries OpenSearch Serverless for similar images, and returns
matched part details from DynamoDB.
"""

import base64
import json
import os

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "")
INDEX_NAME = os.environ.get("INDEX_NAME", "part-images")
TABLE_NAME = os.environ.get("TABLE_NAME", "parts-catalog")
REGION = os.environ.get("AWS_REGION", "us-east-1")
TOP_K = 5

bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


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


def search_similar_images(os_client, embedding: list[float], k: int = TOP_K):
    query = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": k,
                }
            }
        },
    }
    response = os_client.search(index=INDEX_NAME, body=query)
    return response["hits"]["hits"]


def get_part_details(part_number: str) -> dict:
    response = table.get_item(Key={"part_number": part_number})
    return response.get("Item", {})


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

        # Search for similar images
        os_client = get_opensearch_client()
        hits = search_similar_images(os_client, embedding)

        # Fetch part details for each match
        matches = []
        seen_parts = set()
        for hit in hits:
            part_number = hit["_source"]["part_number"]
            if part_number in seen_parts:
                continue
            seen_parts.add(part_number)

            score = hit.get("_score", 0)
            details = get_part_details(part_number)

            if details:
                matches.append({
                    "part_number": part_number,
                    "confidence_score": round(float(score), 4),
                    "title": details.get("title", ""),
                    "description": details.get("description", ""),
                    "brand": details.get("brand", ""),
                    "mfg_number": details.get("mfg_number", ""),
                    "url": details.get("url", ""),
                    "specifications": details.get("specifications", {}),
                    "pricing": details.get("pricing", "Sign in required"),
                    "catalog_page": details.get("catalog_page", ""),
                    "datasheets": details.get("datasheets", []),
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
