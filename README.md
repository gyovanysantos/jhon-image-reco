# HVAC Part Image Recognition

An end-to-end AWS-powered application that recognizes HVAC parts from images. Upload a photo of an HVAC component, and the system finds the closest match in a vectorized image database and returns detailed product information. Built on the Johnstone Supply product catalog.

> **Live App**: https://d1o7hcecd8nn1.cloudfront.net  
> **API Endpoint**: https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/

---

## How It Works

1. **Upload** a photo of an HVAC part (camera or file upload)
2. The image is **vectorized** using Amazon Bedrock (Titan Multimodal Embeddings)
3. The vector is compared against **100 pre-indexed HVAC parts** using cosine similarity
4. The **top 5 matches** are returned with full specifications, brand, and product links

---

## Architecture

```
┌─────────────┐     ┌────────────┐     ┌────────────────┐
│ PDF Catalog  │────▶│  pdfplumber│────▶│ CSV (100 parts)│
│ (1466 pages) │     │  (Python)  │     │ in S3          │
└─────────────┘     └────────────┘     └───────┬────────┘
                                                │
                                                ▼
                                       ┌────────────────┐
                                       │  Scrapy Spider  │
                                       │  (ECS Fargate)  │
                                       └───────┬────────┘
                                               │
                                  ┌────────────┼───────────┐
                                  ▼            ▼           ▼
                            ┌──────────┐ ┌─────────┐ ┌──────────┐
                            │ Images   │ │  JSON   │ │ DynamoDB │
                            │ (S3)     │ │  (S3)   │ │  Table   │
                            └────┬─────┘ └─────────┘ └──────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │  Bedrock Titan     │
                       │  Multimodal Embed. │
                       │  (1024 dimensions) │
                       └────────┬──────────┘
                                │
                                ▼
                       ┌───────────────────┐
                       │  DynamoDB         │
                       │  (binary float32  │
                       │   embeddings)     │
                       └───────────────────┘


  ┌──────────────────────────────────────────────────────────────────┐
  │                     Web Application                              │
  │                                                                  │
  │  Camera / Upload ──▶ POST /api/recognize                        │
  │       │                       │                                  │
  │       │              Bedrock: vectorize query image               │
  │       │                       │                                  │
  │       │              DynamoDB: cosine similarity scan             │
  │       │                       │                                  │
  │       ◀─── Result Overlay ◀───┘                                  │
  │  (title, specs, brand, mfg #, confidence %, product URL)         │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| PDF Extraction | Python + pdfplumber | Reliable extraction of hyperlinks from product catalog |
| Web Scraping | Scrapy on ECS Fargate | Production-grade scraping with rate limiting and pipelines |
| Image Storage | Amazon S3 | Scalable, versioned object storage |
| Structured Data | Amazon DynamoDB | Fast key-value lookups, pay-per-request billing |
| Image Embeddings | Amazon Bedrock (Titan Multimodal v1) | 1024-dim vectors, no GPU infrastructure to manage |
| Vector Search | DynamoDB + cosine similarity (Lambda) | **~$700/month savings** vs OpenSearch Serverless |
| Backend API | API Gateway + AWS Lambda | Serverless, auto-scaling, pay-per-invocation |
| Frontend | React 18 + Vite + TailwindCSS + TypeScript | Modern SPA with camera access and drag-and-drop upload |
| Hosting | CloudFront + S3 | Global CDN with HTTPS |
| Infrastructure | AWS CDK (TypeScript) | Type-safe infrastructure as code |

---

## Project Structure

```
jhon-image-reco/
├── scripts/
│   ├── extract_parts.py           # Phase 1: PDF → CSV extraction
│   ├── upload_csv_to_s3.py        # Phase 1: Upload CSV to S3
│   └── batch_vectorize.py         # Phase 3: Bulk image → embeddings
├── scraper/
│   ├── Dockerfile
│   └── scraper/
│       ├── spiders/
│       │   └── johnstone_spider.py    # Scrapy spider
│       ├── pipelines.py              # S3 + DynamoDB pipelines
│       └── settings.py
├── functions/
│   ├── recognize_handler.py       # Lambda: image recognition
│   ├── parts_handler.py           # Lambda: part lookup
│   └── requirements.txt
├── api/
│   └── server.py                  # Local FastAPI dev server
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/client.ts
│   │   └── components/
│   │       ├── CameraView.tsx
│   │       ├── UploadView.tsx
│   │       ├── ResultOverlay.tsx
│   │       └── PartDetails.tsx
│   ├── vite.config.ts
│   └── package.json
├── infra/
│   ├── bin/app.ts
│   └── lib/
│       ├── storage-stack.ts       # S3 bucket
│       ├── scraper-stack.ts       # ECS + ECR + DynamoDB
│       ├── api-stack.ts           # API Gateway + Lambdas
│       └── frontend-stack.ts      # CloudFront + S3
├── ARCHITECTURE.md
├── TECH-STACK.md
├── LEARNING.md
└── SOLUTION_PROPOSAL.md
```

---

## API Reference

### `POST /api/recognize`

Upload a base64-encoded image to find matching HVAC parts.

**Request**:
```json
{
  "image": "<base64-encoded-image>"
}
```

**Response** (200):
```json
{
  "matches": [
    {
      "part_number": "L51-016",
      "confidence_score": 0.3917,
      "title": "AquaPUMP Variable Speed Stainless Steel Circulator",
      "brand": "Resideo",
      "mfg_number": "PCVF-ECM2020-LF/U",
      "url": "https://www.johnstonesupply.com/product-view?pID=L51-016",
      "specifications": { "Volts": "120", "Max. Flow": "20 GPM", ... },
      "image_s3_key": "images/L51-016/L51-016_0.jpg"
    }
  ]
}
```

### `GET /api/parts/{part_number}`

Get full details for a specific part.

---

## AWS Infrastructure (CDK)

All resources are managed by 4 CDK stacks:

| Stack | Resources | Status |
|-------|-----------|--------|
| `JhonImageRecoStorage` | S3 bucket (versioned, encrypted) | ✅ Deployed |
| `JhonImageRecoScraper` | ECS Fargate cluster, ECR repo, DynamoDB table | ✅ Deployed |
| `JhonImageRecoApi` | API Gateway REST API, 2 Lambda functions | ✅ Deployed |
| `JhonImageRecoFrontend` | CloudFront distribution, S3 static site | ✅ Deployed |

### Estimated Monthly Cost (Dev/Test)

| Service | Est. Cost |
|---------|-----------|
| S3 (~1 GB) | < $1 |
| DynamoDB (100 items, on-demand) | < $1 |
| Bedrock (per-query embeddings) | < $5 |
| Lambda + API Gateway | < $1 |
| CloudFront | < $1 |
| ECS Fargate (one-time scraper) | < $1 |
| **Total** | **~$10/month** |

> **Cost decision**: We replaced OpenSearch Serverless (~$700/month minimum) with DynamoDB + pure-Python cosine similarity in Lambda. For 100 parts, the brute-force scan takes < 1ms and costs virtually nothing.

---

## Prerequisites

- **AWS Account** with permissions for S3, DynamoDB, Lambda, API Gateway, CloudFront, Bedrock, ECS, ECR
- **AWS CLI** configured (`aws configure`)
- **Node.js** 18+ (CDK and frontend)
- **Python** 3.11+ (scripts, Lambda handlers)
- **AWS CDK CLI**: `npm install -g aws-cdk`

---

## Quick Start

### Deploy to AWS

```bash
# 1. Clone and install
git clone https://github.com/gyovanysantos/jhon-image-reco.git
cd jhon-image-reco

# 2. Deploy all infrastructure
cd infra && npm install
npx cdk bootstrap   # first time only
npx cdk deploy --all --require-approval never

# 3. Run data pipeline (one-time)
cd ..
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install pdfplumber boto3 scrapy requests

python scripts/extract_parts.py          # PDF → CSV
python scripts/upload_csv_to_s3.py       # CSV → S3
cd scraper && scrapy crawl johnstone     # Scrape product pages
cd ..
python scripts/batch_vectorize.py        # Images → Bedrock → DynamoDB embeddings

# 4. Build and deploy frontend
cd frontend && npm install
VITE_API_URL=https://<your-api-id>.execute-api.us-east-2.amazonaws.com/prod npm run build
cd ../infra && npx cdk deploy JhonImageRecoFrontend
```

### Local Development

```bash
# API server (port 3001)
cd jhon-image-reco
.venv/Scripts/activate
uvicorn api.server:app --host 127.0.0.1 --port 3001

# Frontend (port 5173, proxies /api → :3001)
cd frontend
npm run dev -- --port 5173

# Open http://localhost:5173
```

---

## DynamoDB Table Schema

**Table**: `parts-catalog` | **Partition Key**: `part_number` (String)

| Attribute | Type | Description |
|-----------|------|-------------|
| `part_number` | String | Johnstone Supply order # (e.g., `S81-007`) |
| `title` | String | Product title |
| `brand` | String | Manufacturer brand |
| `mfg_number` | String | Manufacturer part number |
| `url` | String | Product page URL |
| `specifications` | Map | All specs (HP, Volts, RPM, etc.) |
| `image_s3_key` | String | S3 key for the product image |
| `embedding` | Binary | 1024-dim float32 vector (4096 bytes) |
| `catalog_page` | Number | Page in PDF catalog |
| `datasheets` | List | URLs to spec sheets and manuals |

---

## License

Private — All rights reserved.
