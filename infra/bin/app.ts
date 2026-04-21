#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { StorageStack } from '../lib/storage-stack';
import { ScraperStack } from '../lib/scraper-stack';
import { VectorStack } from '../lib/vector-stack';
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

// Phase 3: Vector search (OpenSearch Serverless + Lambda)
const vector = new VectorStack(app, 'JhonImageRecoVector', {
  env,
  dataBucket: storage.dataBucket,
});

// Phase 4a: API (API Gateway + Lambda)
new ApiStack(app, 'JhonImageRecoApi', {
  env,
  partsTable: scraper.partsTable,
  opensearchEndpoint: vector.opensearchEndpoint,
});

// Phase 4b: Frontend (CloudFront + S3)
new FrontendStack(app, 'JhonImageRecoFrontend', { env });
