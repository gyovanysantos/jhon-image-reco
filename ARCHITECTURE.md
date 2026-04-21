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
                             DynamoDB (binary embedding
                             attribute on parts-catalog)
```

## Query Flow

```
User Camera/Upload
       │
       ▼
  API Gateway ──▶ Lambda (recognize_handler)
                        │
                        ├─▶ Bedrock: vectorize query image (us-east-1)
                        │
                        ├─▶ DynamoDB: scan embeddings + cosine similarity
                        │
                        └─▶ Return top-K matches with part details
                                │
                                ▼
                         JSON response ──▶ Frontend overlay
```

## Infrastructure

All AWS resources managed by **CDK (TypeScript)** in `infra/`.

| Stack | Resources | Status |
|-------|-----------|--------|
| StorageStack | S3 bucket | ✅ Deployed |
| ScraperStack | ECS Fargate task (Scrapy), ECR repo, DynamoDB table | ✅ Deployed |
| ApiStack | API Gateway, recognition Lambda, parts Lambda | ✅ Deployed |
| FrontendStack | CloudFront distribution, S3 static hosting | ✅ Deployed |

## Live URLs

| Service | URL |
|---------|-----|
| Frontend (CloudFront) | https://d1o7hcecd8nn1.cloudfront.net |
| API Gateway | https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/ |
| POST /api/recognize | https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/api/recognize |
| GET /api/parts/{pn} | https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/api/parts/{part_number} |

> **Note:** VectorStack was removed — embeddings are stored directly in DynamoDB
> as binary attributes. Cosine similarity is computed in the Lambda function.
> This saves ~$700/month vs OpenSearch Serverless for small datasets (<10K vectors).

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `scripts/` | One-off data pipeline scripts (extract, upload, batch vectorize) |
| `scraper/` | Scrapy project with Dockerfile for ECS Fargate |
| `functions/` | AWS Lambda handler code |
| `frontend/` | React + Vite + TailwindCSS AR web app |
| `infra/` | CDK stacks (TypeScript) |
| `output/` | Generated artifacts (CSV, not committed to git) |
