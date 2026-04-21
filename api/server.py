"""
Local development API server for HVAC Part Recognition.

Reuses the same logic as the Lambda handlers (recognize_handler.py, parts_handler.py)
but runs locally via FastAPI + Uvicorn.

Usage:
    cd jhon-image-reco
    .venv/Scripts/python -m uvicorn api.server:app --reload --port 3001
"""

import base64
import json
import math
import struct
from decimal import Decimal

import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
TABLE_NAME = "parts-catalog"
AWS_REGION = "us-east-2"
BEDROCK_REGION = "us-east-1"
TOP_K = 5

# --- AWS Clients (initialized once) ---
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)
bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

# --- FastAPI App ---
app = FastAPI(title="HVAC Part Recognition API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class RecognizeRequest(BaseModel):
    image: str  # base64 encoded image


# --- Helper functions (same logic as Lambda handlers) ---
def get_image_embedding(image_bytes: bytes) -> list[float]:
    """Generate 1024-dim embedding via Bedrock Titan Multimodal."""
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
    """Unpack binary float32 LE back to list of floats."""
    n = len(data) // 4
    return list(struct.unpack(f"<{n}f", data))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def decimal_default(obj):
    """JSON serializer for Decimal types from DynamoDB."""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def clean_item(item: dict) -> dict:
    """Remove binary fields and convert Decimals for JSON response."""
    cleaned = {}
    for k, v in item.items():
        if k == "embedding":
            continue  # skip binary embedding
        if isinstance(v, Decimal):
            cleaned[k] = float(v) if v % 1 else int(v)
        elif isinstance(v, bytes):
            continue
        elif hasattr(v, "value") and isinstance(v.value, bytes):
            continue
        else:
            cleaned[k] = v
    return json.loads(json.dumps(cleaned, default=decimal_default))


# --- Routes ---
@app.get("/api/health")
def health():
    return {"status": "ok", "table": TABLE_NAME, "region": AWS_REGION}


@app.post("/api/recognize")
def recognize(req: RecognizeRequest):
    """Upload an image (base64) and find matching HVAC parts."""
    # Validate and decode image
    try:
        image_bytes = base64.b64decode(req.image)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # Get embedding from Bedrock
    embedding = get_image_embedding(image_bytes)

    # Scan all items with embeddings from DynamoDB
    response = table.scan(
        FilterExpression="attribute_exists(embedding)",
    )
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression="attribute_exists(embedding)",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    # Compute cosine similarity for each item
    scored = []
    for item in items:
        emb_binary = item.get("embedding")
        if not emb_binary:
            continue
        raw = bytes(emb_binary.value) if hasattr(emb_binary, "value") else bytes(emb_binary)
        stored_embedding = binary_to_embedding(raw)
        score = cosine_similarity(embedding, stored_embedding)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_k = scored[:TOP_K]

    # Build response
    matches = []
    for score, item in top_k:
        cleaned = clean_item(item)
        cleaned["confidence_score"] = round(score, 4)
        matches.append(cleaned)

    return {"matches": matches}


@app.get("/api/parts/{part_number}")
def get_part(part_number: str):
    """Get full details for a specific part number."""
    response = table.get_item(Key={"part_number": part_number})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail=f"Part {part_number} not found")

    return clean_item(item)
