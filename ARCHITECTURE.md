# Architecture

## System Overview

End-to-end HVAC part image recognition pipeline on AWS. Users upload a photo of an HVAC component, the system finds the closest match in a vectorized image database, and returns product details.

## Data Pipeline

```
PDF Catalog ──▶ Python (pdfplumber) ──▶ CSV (100 parts)
                                            │
                                            ▼
                                       S3 Bucket
                                            │
                                            ▼
                                    Scrapy Spider (ECS Fargate)
                                    ┌───────┼───────┐
                                    ▼       ▼       ▼
                                Images   JSON    DynamoDB
                                (S3)     (S3)    (parts table)
                                    │
                                    ▼
                             Bedrock Titan Multimodal
                             Embeddings v1 (1024-dim)
                                    │
                                    ▼
                             OpenSearch Serverless
                             (kNN vector index)
```

## Query Flow

```
User Camera/Upload
       │
       ▼
  API Gateway ──▶ Lambda (recognize_handler)
                        │
                        ├─▶ Bedrock: vectorize query image
                        │
                        ├─▶ OpenSearch: kNN similarity search
                        │
                        └─▶ DynamoDB: fetch part details
                                │
                                ▼
                         JSON response ──▶ Frontend overlay
```

## Infrastructure

All AWS resources managed by **CDK (TypeScript)** in `infra/`.

| Stack | Resources |
|-------|-----------|
| StorageStack | S3 bucket, DynamoDB table |
| ScraperStack | ECS Fargate task (Scrapy), ECR repo |
| VectorStack | OpenSearch Serverless collection, vectorization Lambda |
| ApiStack | API Gateway, recognition Lambda, parts Lambda |
| FrontendStack | CloudFront distribution, S3 static hosting |

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `scripts/` | One-off data pipeline scripts (extract, upload, batch vectorize) |
| `scraper/` | Scrapy project with Dockerfile for ECS Fargate |
| `functions/` | AWS Lambda handler code |
| `frontend/` | React + Vite + TailwindCSS AR web app |
| `infra/` | CDK stacks (TypeScript) |
| `output/` | Generated artifacts (CSV, not committed to git) |
