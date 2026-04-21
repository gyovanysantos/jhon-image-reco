"""
Phase 4a: Lambda handler for part details lookup.

GET /api/parts/{part_number} — returns full part details from DynamoDB.
"""

import json
import os

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "parts-catalog")
REGION = os.environ.get("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def handler(event, context):
    """Lambda handler for GET /api/parts/{part_number}."""
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        part_number = event.get("pathParameters", {}).get("part_number", "")

        if not part_number:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing part_number parameter"}),
            }

        response = table.get_item(Key={"part_number": part_number})
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Part {part_number} not found"}),
            }

        # Convert Decimal types for JSON serialization
        result = json.loads(json.dumps(item, default=str))

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(result),
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Internal server error"}),
        }
