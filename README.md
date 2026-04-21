# HVAC Part Image Recognition — Augmented Reality App

An end-to-end AWS-powered application that recognizes HVAC parts from images and displays product details via an augmented reality web interface. Built on the Johnstone Supply product catalog.

## Overview

| Component | Technology |
|-----------|-----------|
| PDF Extraction | Python + pdfplumber |
| Web Scraping | Scrapy (containerized) |
| Image Storage | Amazon S3 |
| Structured Data | Amazon DynamoDB |
| Image Embeddings | Amazon Bedrock (Titan Multimodal Embeddings v1) |
| Vector Search | Amazon OpenSearch Serverless |
| Backend API | API Gateway + AWS Lambda |
| Frontend | React + Vite (AR webcam overlay) |
| Hosting | Amazon CloudFront + S3 |
| Infrastructure | AWS CDK (TypeScript) |

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  PDF Catalog     │────▶│ Python Script│────▶│ CSV in S3           │
│  (Cat_220)       │     │ (pdfplumber) │     │ (100 part numbers)  │
└─────────────────┘     └──────────────┘     └────────┬────────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Scrapy Spider    │
                                              │ (ECS Fargate)    │
                                              └───────┬──────────┘
                                                      │
                                         ┌────────────┼────────────┐
                                         ▼            ▼            ▼
                                   ┌──────────┐ ┌──────────┐ ┌──────────┐
                                   │ Images   │ │ JSON     │ │ DynamoDB │
                                   │ in S3    │ │ in S3    │ │ Table    │
                                   └────┬─────┘ └──────────┘ └──────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │ Bedrock Titan      │
                              │ Multimodal Embed.  │
                              └────────┬──────────┘
                                       │
                                       ▼
                              ┌───────────────────┐
                              │ OpenSearch         │
                              │ Serverless (kNN)   │
                              └───────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                     AR Web Application                          │
  │                                                                  │
  │  User Camera ──▶ Capture Image ──▶ POST /api/recognize          │
  │       │                                    │                     │
  │       │                                    ▼                     │
  │       │                          Bedrock (vectorize query)       │
  │       │                                    │                     │
  │       │                                    ▼                     │
  │       │                          OpenSearch (kNN similarity)     │
  │       │                                    │                     │
  │       │                                    ▼                     │
  │       │                          DynamoDB (part details)         │
  │       │                                    │                     │
  │       ◀────────── Result Overlay ◀─────────┘                    │
  │  (title, specs, brand, order #, product URL)                    │
  └──────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
jhon-image-reco/
├── Cat_220_linked_p1.pdf              # Source Johnstone Supply catalog
├── scripts/
│   ├── extract_parts.py               # Phase 1: PDF → CSV extraction
│   ├── upload_csv_to_s3.py            # Phase 1: Upload CSV to S3
│   └── batch_vectorize.py             # Phase 3: Bulk image vectorization
├── scraper/
│   ├── scrapy.cfg
│   ├── Dockerfile
│   ├── requirements.txt
│   └── scraper/
│       ├── __init__.py
│       ├── spiders/
│       │   ├── __init__.py
│       │   └── johnstone_spider.py    # Phase 2: Product page spider
│       ├── items.py                   # Scrapy item definitions
│       ├── pipelines.py              # S3 + DynamoDB pipelines
│       └── settings.py
├── functions/
│   ├── recognize_handler.py           # Phase 4: Image recognition Lambda
│   ├── parts_handler.py               # Phase 4: Part lookup Lambda
│   ├── vectorize_images.py            # Phase 3: Vectorization Lambda
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       │   ├── CameraView.tsx
│       │   ├── UploadView.tsx
│       │   ├── ResultOverlay.tsx
│       │   └── PartDetails.tsx
│       └── api/
│           └── client.ts
├── infra/
│   ├── bin/app.ts
│   ├── cdk.json
│   ├── package.json
│   ├── tsconfig.json
│   └── lib/
│       ├── storage-stack.ts
│       ├── scraper-stack.ts
│       ├── vector-stack.ts
│       ├── api-stack.ts
│       └── frontend-stack.ts
└── .gitignore
```

---

## Requirements

### Phase 1 — PDF Extraction & CSV Generation

**Goal**: Extract 100 HVAC part numbers from the Johnstone Supply PDF catalog and produce a structured CSV.

| Requirement | Details |
|-------------|---------|
| Input | `Cat_220_linked_p1.pdf` (Johnstone Supply catalog) |
| Output | `parts_catalog.csv` uploaded to `s3://jhon-image-reco-data/csv/` |
| CSV Columns | `part_number`, `url`, `description`, `catalog_page` |
| URL Format | `https://www.johnstonesupply.com/product-view?pID={part_number}` |
| Part Count | Minimum 100 unique parts |
| Library | `pdfplumber` for PDF text/link extraction |
| Storage | AWS S3 bucket with versioning and AES-256 encryption |

**Steps**:
1. Install dependencies: `pip install pdfplumber boto3`
2. Run `python scripts/extract_parts.py` — parses PDF, produces `output/parts_catalog.csv`
3. Run `python scripts/upload_csv_to_s3.py` — uploads CSV to S3

---

### Phase 2 — Web Scraping with Scrapy

**Goal**: Scrape Johnstone Supply product pages for each part, download product images, and store structured data.

| Requirement | Details |
|-------------|---------|
| Input | CSV from Phase 1 (S3 or local) |
| Spider | Reads CSV, requests each product URL |
| Data Scraped | Title, full specifications, images, Order #, Mfg #, Brand, catalog page, datasheets |
| Image Sources | `johnstonesupply.sirv.com` CDN images + `johnstonesupply.com/images/renderImage` |
| Image Storage | `s3://jhon-image-reco-data/images/{part_number}/` |
| Data Storage | JSON in `s3://jhon-image-reco-data/scraped-data/{part_number}.json` + DynamoDB |
| Politeness | 2-3 second delay between requests, respect `robots.txt` |
| Pricing | Behind auth wall — store as "Sign in required" with link to product page |
| Container | Docker image pushed to ECR, executed via ECS Fargate |

**DynamoDB Table Schema** (`parts-catalog`):

| Attribute | Type | Description |
|-----------|------|-------------|
| `part_number` (PK) | String | Johnstone Supply order number (e.g., `S81-007`) |
| `title` | String | Product title |
| `description` | String | Product description text |
| `brand` | String | Manufacturer brand (e.g., "US Motors") |
| `mfg_number` | String | Manufacturer part number |
| `catalog_page` | Number | Page in PDF catalog |
| `url` | String | Full Johnstone Supply product URL |
| `specifications` | Map | All product specs (HP, Volts, RPM, etc.) |
| `image_keys` | List | S3 keys of downloaded product images |
| `datasheets` | List | URLs to spec sheets, manuals, videos |
| `pricing` | String | "Sign in required" (or price if auth available) |

**Steps**:
1. `cd scraper && pip install -r requirements.txt`
2. Test on 5 parts: `scrapy crawl johnstone -a limit=5`
3. Full run: `scrapy crawl johnstone`
4. Docker build: `docker build -t jhon-scraper .`
5. Push to ECR and run via Fargate (or run locally for dev)

---

### Phase 3 — Image Vectorization

**Goal**: Generate vector embeddings for all scraped product images and index them for similarity search.

| Requirement | Details |
|-------------|---------|
| Embedding Model | Amazon Bedrock `amazon.titan-embed-image-v1` |
| Embedding Dimensions | 1024 |
| Vector Store | Amazon OpenSearch Serverless (vector search collection) |
| Collection | `parts-vectors` |
| Index | `part-images` |
| Similarity Metric | Cosine |
| Trigger | S3 event on new image upload (Lambda) + batch script for initial load |

**OpenSearch Index Mapping**:
```json
{
  "mappings": {
    "properties": {
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "part_number": { "type": "keyword" },
      "image_s3_key": { "type": "keyword" }
    }
  }
}
```

**Steps**:
1. Deploy CDK vector stack (OpenSearch Serverless collection + Lambda)
2. Run batch vectorization: `python scripts/batch_vectorize.py`
3. Verify: query OpenSearch with a known image embedding, confirm correct part returned

---

### Phase 4 — Augmented Reality Web Application

**Goal**: Build a camera-based web app that recognizes HVAC parts in real-time and overlays product details.

#### 4a. Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recognize` | POST | Accepts image (base64 JSON), vectorizes via Bedrock, queries OpenSearch kNN (top-5), returns matched parts with details from DynamoDB |
| `/api/parts/{part_number}` | GET | Returns full part details from DynamoDB |

**Recognition Response Shape**:
```json
{
  "matches": [
    {
      "part_number": "S81-007",
      "confidence_score": 0.94,
      "title": "Replacement for Armstrong/Ducane/Goodman and Lennox Condenser Fan Motor",
      "brand": "US Motors",
      "mfg_number": "2243",
      "url": "https://www.johnstonesupply.com/product-view?pID=S81-007",
      "specifications": {
        "HP": "1/10",
        "Volts": "208-230",
        "RPM": "1075",
        "Phase": "1",
        "Diameter": "5\""
      },
      "pricing": "Sign in required",
      "catalog_page": 65
    }
  ]
}
```

#### 4b. Frontend (React + Vite)

| Component | Purpose |
|-----------|---------|
| `CameraView` | Webcam feed using `react-webcam`, capture button, real-time preview |
| `UploadView` | Drag-and-drop image upload as alternative to camera |
| `ResultOverlay` | Semi-transparent card overlaid on camera view showing matched part info |
| `PartDetails` | Expandable detail panel with full specifications, datasheets, product link |

**User Flow**:
1. User opens web app (mobile or desktop)
2. Camera permission requested and activated
3. User points camera at HVAC part **or** uploads a photo
4. Image captured and sent to `POST /api/recognize`
5. Loading spinner while processing
6. **Match found**: Overlay card shows — part title, key specs, brand, order #, link to Johnstone Supply
7. **No match**: "Part not recognized — try another angle" message
8. User can tap overlay to expand full specifications and datasheets

**Frontend Tech Stack**:
- React 18 + TypeScript
- Vite (build tool)
- `react-webcam` (camera access)
- TailwindCSS (styling)
- Hosted on CloudFront + S3

**Steps**:
1. `cd frontend && npm install`
2. `npm run dev` — local development
3. `npm run build` — production build
4. Deploy to S3 + CloudFront via CDK

---

### Phase 5 — Infrastructure as Code (CDK)

**Goal**: All AWS resources defined and deployed via CDK (TypeScript).

| Stack | Resources |
|-------|-----------|
| `StorageStack` | S3 bucket (`jhon-image-reco-data`) with versioning, encryption, lifecycle rules |
| `ScraperStack` | ECR repository, ECS Fargate task definition, DynamoDB table (`parts-catalog`), IAM roles |
| `VectorStack` | OpenSearch Serverless collection (`parts-vectors`), vectorization Lambda, Bedrock IAM policy, S3 event trigger |
| `ApiStack` | API Gateway REST API, recognition Lambda, parts Lambda, CORS config |
| `FrontendStack` | S3 bucket (static site), CloudFront distribution, OAI |

**Steps**:
1. `cd infra && npm install`
2. `npx cdk synth` — validate all stacks
3. `npx cdk deploy --all` — deploy everything
4. Grab API Gateway URL from outputs, configure frontend `.env`

---

## AWS Services & Estimated Costs (Dev/Test)

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| S3 | ~1 GB storage (images + data) | < $1 |
| DynamoDB | 100 items, on-demand | < $1 |
| OpenSearch Serverless | 2 OCU minimum | ~$70 |
| Bedrock (Titan Embeddings) | ~500 image embeddings | < $5 |
| Lambda | Low invocation count | < $1 |
| API Gateway | Low request count | < $1 |
| CloudFront | Low traffic | < $1 |
| ECS Fargate | One-time scraper run | < $1 |
| **Total** | | **~$80/month** |

> **Note**: OpenSearch Serverless has a minimum cost of ~$70/month (2 OCUs). For cost optimization in dev, consider using OpenSearch provisioned (t3.small) or pgvector on RDS.

## Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured (`aws configure`)
- **Node.js** 18+ (for CDK and frontend)
- **Python** 3.11+ (for scripts, scraper, Lambdas)
- **Docker** (for Scrapy containerization)
- **AWS CDK CLI**: `npm install -g aws-cdk`

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/gyovanysantos/jhon-image-reco.git
cd jhon-image-reco

# 2. Deploy infrastructure
cd infra && npm install && npx cdk deploy --all

# 3. Extract parts from PDF
cd ../scripts && pip install -r requirements.txt
python extract_parts.py
python upload_csv_to_s3.py

# 4. Run scraper
cd ../scraper && pip install -r requirements.txt
scrapy crawl johnstone

# 5. Vectorize images
python ../scripts/batch_vectorize.py

# 6. Start frontend
cd ../frontend && npm install && npm run dev
```

## License

Private — All rights reserved.
