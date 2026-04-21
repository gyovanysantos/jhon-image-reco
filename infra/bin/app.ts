#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { StorageStack } from '../lib/storage-stack';
import { ScraperStack } from '../lib/scraper-stack';
import { ApiStack } from '../lib/api-stack';
import { FrontendStack } from '../lib/frontend-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Phase 1: Storage (S3 bucket)
const storage = new StorageStack(app, 'JhonImageRecoStorage', { env });

// Phase 2: Scraper (ECR + Fargate + DynamoDB)
const scraper = new ScraperStack(app, 'JhonImageRecoScraper', {
  env,
  dataBucket: storage.dataBucket,
});

// Phase 3: Vectorization done via batch script (scripts/batch_vectorize.py)
// Embeddings stored directly in DynamoDB (no OpenSearch needed for 100 images)

// Phase 4a: API (API Gateway + Lambda)
new ApiStack(app, 'JhonImageRecoApi', {
  env,
  partsTable: scraper.partsTable,
  dataBucket: storage.dataBucket,
});

// Phase 4b: Frontend (CloudFront + S3)
new FrontendStack(app, 'JhonImageRecoFrontend', { env });
