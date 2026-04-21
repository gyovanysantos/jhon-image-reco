# Task Plan

## Phase 1: PDF Extraction → CSV
- [x] Extract 100 parts from `Cat_220_linked_p1.pdf`
- [x] Generate `output/parts_catalog.csv`
- [x] Upload CSV to S3

## Phase 2: Web Scraping
- [x] Deploy CDK StorageStack (S3 bucket)
- [x] Deploy CDK ScraperStack (DynamoDB table, ECR, VPC, ECS)
- [x] Upload CSV to S3
- [x] Fix spider selectors (title, brand, mfg#, specs, images)
- [x] Test spider on 5 parts (dry run + full pipeline)
- [x] Run full scrape (100 parts → images + JSON + DynamoDB)

## Phase 3: Image Vectorization
- [x] ~~Deploy VectorStack~~ → Removed OpenSearch ($700/mo), using DynamoDB instead
- [x] Enable Bedrock Titan Multimodal Embeddings (us-east-1, cross-region)
- [x] Run batch vectorization (100 images → 1024-dim embeddings in DynamoDB)
- [x] Verify embeddings (100/100 items with binary embedding attribute)
- [x] End-to-end similarity test (motors match motors, thermostats rank low)

## Phase 4: AR Web App + API
- [x] Create local FastAPI server (api/server.py, port 3001)
- [x] Install frontend dependencies (React, Vite, TailwindCSS)
- [x] Configure Vite proxy (/api → localhost:3001)
- [x] Test local recognize endpoint (5 matches returned correctly)
- [x] Deploy ApiStack (API Gateway, Lambda handlers)
- [x] Fix DynamoDB reserved keyword issue (`url` → `#u` alias)
- [x] Build React frontend for production (VITE_API_URL baked in)
- [x] Fix TypeScript build error (added `vite/client` types)
- [x] Deploy FrontendStack (CloudFront + S3)
- [x] End-to-end cloud test (5 matches returned from live API)

## Live URLs
- Frontend: https://d1o7hcecd8nn1.cloudfront.net
- API: https://qowayc83di.execute-api.us-east-2.amazonaws.com/prod/

## Phase 5: Polish & Deploy
- [ ] Performance tuning (cold starts, image sizes)
- [ ] Error handling and retry logic
- [ ] Documentation and demo
