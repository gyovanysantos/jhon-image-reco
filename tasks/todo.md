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
- [ ] Deploy VectorStack (OpenSearch Serverless collection)
- [ ] Run batch vectorization script on scraped images
- [ ] Verify kNN index in OpenSearch

## Phase 4: AR Web App + API
- [ ] Deploy ApiStack (API Gateway, Lambda handlers)
- [ ] Build React frontend
- [ ] Deploy FrontendStack (CloudFront + S3)
- [ ] End-to-end test: upload image → get part result

## Phase 5: Polish & Deploy
- [ ] Performance tuning (cold starts, image sizes)
- [ ] Error handling and retry logic
- [ ] Documentation and demo
