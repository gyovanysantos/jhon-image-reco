# Solution Proposal: HVAC Part Image Recognition System

**Prepared by**: Nathan Eaves, Jaime DelValle, Gyovany Santos  
**Date**: April 2026  
**Client**: Johnstone Supply  
**Status**: ✅ Delivered — Proof of Concept Live

---

## 1. Executive Summary

This document presents the design and implementation of an **image-based HVAC part recognition system**. A field technician can upload or photograph an HVAC component, and the system instantly identifies the part, returning product specifications, manufacturer info, and a direct link to order it from Johnstone Supply.

The solution is fully serverless, runs on AWS, and currently indexes **100 HVAC parts** as a proof of concept — designed to scale to **10,000+ parts** with minimal changes.

> **Live Demo**: https://d1o7hcecd8nn1.cloudfront.net

---

## 2. Problem Statement

HVAC technicians in the field often need to identify parts they're looking at — to find replacement specs, order numbers, or compatible alternatives. Today this requires:

1. Manually searching catalogs (1,400+ page PDF)
2. Calling a distributor with a physical description
3. Googling manufacturer part numbers stamped on the equipment

This process is **slow** (10–30 minutes per part lookup), **error-prone** (wrong part ordered due to similar models), and **costly** (truck rolls for wrong parts, technician downtime).

### What We Solve

| Pain Point | Our Solution |
|-----------|-------------|
| "What part is this?" | Upload a photo → instant identification |
| "What are the specs?" | Full specifications returned (HP, Volts, RPM, etc.) |
| "Where do I order it?" | Direct link to Johnstone Supply product page |
| "Is there a compatible replacement?" | Similarity-ranked results show related parts |

---

## 3. Solution Architecture

### 3.1 High-Level Flow

```
  ┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
  │  Technician   │         │  Cloud Backend    │         │  Data Store  │
  │  (Mobile/Web) │         │  (Serverless)     │         │  (AWS)       │
  └──────┬───────┘         └────────┬─────────┘         └──────┬───────┘
         │                          │                           │
         │  1. Upload photo         │                           │
         │─────────────────────────▶│                           │
         │                          │  2. Vectorize image       │
         │                          │──────────────────────────▶│ Bedrock
         │                          │                           │
         │                          │  3. Search similar vectors│
         │                          │──────────────────────────▶│ DynamoDB
         │                          │                           │
         │  4. Return matches       │  (cosine similarity)      │
         │◀─────────────────────────│◀──────────────────────────│
         │                          │                           │
         │  5. Display results      │                           │
         │  (specs, brand, link)    │                           │
         └──────────────────────────┘                           │
```

### 3.2 The Data Pipeline (One-Time Setup)

Building the knowledge base is a **4-step pipeline** that runs once (and can be re-run to refresh data):

| Step | Input | Process | Output |
|------|-------|---------|--------|
| **1. Extract** | 1,466-page PDF catalog | Python + pdfplumber extracts product links | CSV with 100 part numbers |
| **2. Scrape** | Part number list | Scrapy spider visits each product page | Images, specs, and metadata in S3 + DynamoDB |
| **3. Vectorize** | Product images in S3 | Amazon Bedrock generates 1024-dim embeddings | Binary vectors stored in DynamoDB |
| **4. Deploy** | CDK stacks | Infrastructure as Code deploys everything | Live API + web app |

### 3.3 The Query Flow (Per User Request)

When a user uploads an image:

1. **API Gateway** receives the image (base64 encoded, max 10 MB)
2. **Lambda** sends the image to **Amazon Bedrock** (Titan Multimodal Embeddings v1)
3. Bedrock returns a **1024-dimensional vector** representing the image
4. Lambda **scans DynamoDB** for all stored embeddings
5. **Cosine similarity** is computed in pure Python (no external libraries)
6. The **top 5 matches** are returned with full product details
7. Frontend displays results as an overlay with confidence scores

**Response time**: ~2–3 seconds (dominated by Bedrock inference)

---

## 4. Technology Decisions

### 4.1 Why DynamoDB Instead of OpenSearch?

The original design used **Amazon OpenSearch Serverless** for vector search. During implementation, we discovered:

| Factor | OpenSearch Serverless | DynamoDB + Lambda |
|--------|----------------------|-------------------|
| **Minimum cost** | ~$700/month (4 OCUs) | ~$1/month |
| **Complexity** | VPC, security policies, index management | Single table, no extra service |
| **Performance (100 parts)** | < 10ms kNN search | < 1ms brute-force scan |
| **Performance (10K parts)** | < 10ms kNN search | ~50ms brute-force scan |
| **Scaling limit** | Millions of vectors | ~10K vectors before needing a dedicated vector DB |

**Decision**: For the current dataset (100 parts, scaling to ~10K), DynamoDB is **70x cheaper** with equivalent performance. If the catalog grows beyond 10K parts, we can migrate to OpenSearch or pgvector.

### 4.2 Why Bedrock Titan Multimodal?

| Factor | Details |
|--------|---------|
| **No GPU infrastructure** | Fully managed API — no EC2 instances to provision |
| **Multimodal** | Same model handles both images and text |
| **High quality** | 1024-dim embeddings capture fine-grained visual features |
| **Pay per use** | ~$0.0006 per image — 1000 queries costs $0.60 |

### 4.3 Why Serverless?

| Factor | Details |
|--------|---------|
| **Zero idle cost** | Lambda + API Gateway + DynamoDB on-demand = pay only for actual usage |
| **Auto-scaling** | Handles 0 to 1000 concurrent users without configuration |
| **No servers** | No patching, no SSH, no container orchestration for the API layer |
| **Global CDN** | CloudFront serves frontend from edge locations worldwide |

---

## 5. What's Been Delivered

### 5.1 Working System

| Component | Status | Details |
|-----------|--------|---------|
| PDF extraction pipeline | ✅ Complete | 100 parts extracted from 1,466-page catalog |
| Web scraper | ✅ Complete | 100 product pages scraped (images, specs, metadata) |
| Image vectorization | ✅ Complete | 100 images converted to 1024-dim embeddings |
| REST API | ✅ Deployed | POST /api/recognize + GET /api/parts/{pn} |
| Web application | ✅ Deployed | Camera capture + file upload + results overlay |
| Infrastructure (CDK) | ✅ Deployed | 4 CloudFormation stacks, fully reproducible |

### 5.2 Live URLs

| Resource | URL |
|----------|-----|
| **Web App** | https://d1o7hcecd8nn1.cloudfront.net |
| **API** | https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/ |
| **GitHub** | https://github.com/gyovanysantos/jhon-image-reco |

### 5.3 AWS Resources Deployed

| Resource | Name / ARN |
|----------|-----------|
| S3 Bucket | `jhon-image-reco-data-424009524696` |
| DynamoDB Table | `parts-catalog` (100 items with embeddings) |
| Lambda (recognize) | `jhon-recognize` (512 MB, 30s timeout) |
| Lambda (parts) | `jhon-parts` (256 MB, 10s timeout) |
| API Gateway | `HVAC Parts Recognition API` |
| CloudFront | `d1o7hcecd8nn1.cloudfront.net` |
| Region | `us-east-2` (Bedrock cross-region to `us-east-1`) |

---

## 6. Cost Analysis

### Current (Proof of Concept — 100 parts)

| Service | Monthly Cost |
|---------|-------------|
| S3 (images + frontend) | < $1 |
| DynamoDB (on-demand, 100 items) | < $1 |
| Lambda (low traffic) | < $1 |
| API Gateway (low traffic) | < $1 |
| Bedrock (per-query) | < $5 |
| CloudFront | < $1 |
| **Total** | **~$10/month** |

### Projected (Production — 10K parts, 1K queries/day)

| Service | Monthly Cost |
|---------|-------------|
| S3 (~10 GB) | ~$3 |
| DynamoDB (10K items, provisioned) | ~$10 |
| Lambda (~30K invocations) | ~$5 |
| API Gateway (~30K requests) | ~$3 |
| Bedrock (~30K embeddings) | ~$18 |
| CloudFront (moderate traffic) | ~$5 |
| **Total** | **~$44/month** |

> Compare: OpenSearch Serverless alone would cost $700+/month.

---

## 7. Scaling Roadmap

### Phase 2: Full Catalog (Next)

| Item | Details |
|------|---------|
| **Expand to full catalog** | Run scraper on all ~5,000+ parts in the PDF |
| **Incremental updates** | Re-scrape only new/changed products |
| **Better matching** | Fine-tune confidence thresholds, filter by category |

### Phase 3: Production Features

| Item | Details |
|------|---------|
| **Authentication** | Add Cognito user pools for technician login |
| **Search history** | Store past lookups per user for quick re-orders |
| **Text search** | Allow searching by part name, brand, or specs |
| **Offline mode** | Cache recently viewed parts for areas with poor connectivity |
| **Mobile app** | React Native wrapper for a native mobile experience |

### Phase 4: Advanced AI

| Item | Details |
|------|---------|
| **Multi-angle matching** | Accept multiple photos for higher accuracy |
| **Compatibility engine** | "This part can replace X, Y, Z" recommendations |
| **Damage detection** | Identify worn or damaged parts and suggest replacements |
| **Voice assistant** | "What part is this?" via voice + camera |

### Scaling the Vector Store

| Parts Count | Recommended Store | Est. Search Time |
|-------------|------------------|-----------------|
| < 1,000 | DynamoDB (current) | < 1ms |
| 1,000–10,000 | DynamoDB (current) | < 50ms |
| 10,000–100,000 | PostgreSQL + pgvector | < 20ms |
| 100,000+ | OpenSearch Serverless | < 10ms |

---

## 8. Security

| Concern | Mitigation |
|---------|-----------|
| **Data in transit** | HTTPS everywhere (CloudFront, API Gateway) |
| **Data at rest** | S3 encryption (AES-256), DynamoDB encryption (AWS-managed) |
| **API access** | CORS restricted, input validation (max 10 MB, base64 checks) |
| **Infrastructure** | Least-privilege IAM roles, no hardcoded credentials |
| **Frontend** | S3 bucket with BlockPublicAccess, served only via CloudFront OAC |
| **Dependencies** | Minimal Lambda dependencies (boto3 only, no third-party packages) |

---

## 9. Conclusion

This proof of concept demonstrates that **HVAC part recognition via image upload** is technically feasible, cost-effective, and ready for production scaling. The key achievements:

1. **Works today** — live at https://d1o7hcecd8nn1.cloudfront.net
2. **Costs ~$10/month** — vs $700+ with traditional vector search infrastructure
3. **Fully serverless** — zero servers to manage, auto-scales to demand
4. **Reproducible** — entire infrastructure defined as code (CDK), deployable in one command
5. **Extensible** — designed to scale from 100 to 10,000+ parts with the same architecture

The system is ready for stakeholder demo and feedback to prioritize the Phase 2 roadmap items.
