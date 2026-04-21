# Tech Stack

## Data Pipeline

| Technology | Version | Why |
|-----------|---------|-----|
| **Python** | 3.14.3 | Primary language for scripts and Lambda functions |
| **uv** | 0.11.2 | Fast Python package manager, manages venv and deps |
| **pdfplumber** | 0.11.9 | Extracts text and annotation hyperlinks from PDF catalogs |
| **Scrapy** | 2.11+ | Production-grade web scraping framework with built-in rate limiting and pipeline system |
| **boto3** | 1.42.93 | AWS SDK for Python — S3 uploads, DynamoDB writes, Bedrock inference |

## AWS Services

| Service | Why |
|---------|-----|
| **Amazon S3** | Stores CSV, scraped images, JSON data, and frontend static files |
| **Amazon DynamoDB** | NoSQL store for structured part data (fast key-value lookups by part number) |
| **Amazon Bedrock** | Titan Multimodal Embeddings v1 — generates 1024-dim vectors from images |
| ~~Amazon OpenSearch Serverless~~ | Removed — DynamoDB + Lambda cosine similarity is cheaper for <10K vectors |
| **AWS Lambda** | Serverless compute for API handlers and image vectorization |
| **Amazon API Gateway** | REST API endpoint for the frontend |
| **Amazon CloudFront** | CDN for frontend static assets |
| **Amazon ECS Fargate** | Runs Scrapy spider container (no server management) |
| **Amazon ECR** | Docker image registry for scraper container |

## Frontend

| Technology | Version | Why |
|-----------|---------|-----|
| **React** | 18.x | Component-based UI with good ecosystem for camera/media APIs |
| **Vite** | 5.x | Fast dev server and build tool for React |
| **TypeScript** | 5.x | Type safety for frontend code |
| **TailwindCSS** | 3.x | Utility-first CSS for rapid UI development |

## Infrastructure

| Technology | Version | Why |
|-----------|---------|-----|
| **AWS CDK** | 2.x (TypeScript) | Infrastructure as code — type-safe, composable stacks |
| **Docker** | — | Containerizes Scrapy spider for ECS Fargate deployment |

## Dev Tools

| Tool | Why |
|------|-----|
| **Git + GitHub** | Version control, repo at github.com/gyovanysantos/jhon-image-reco |
