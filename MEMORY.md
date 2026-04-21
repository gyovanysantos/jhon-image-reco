# Project Memory

## Current State
- **Phase 1 (PDF Extraction)**: COMPLETE — 100 parts extracted to `output/parts_catalog.csv`
- **Phase 2 (Scraping)**: COMPLETE — 100 parts scraped, images + JSON in S3, data in DynamoDB
- **Phase 3 (Vectorization)**: COMPLETE — 100 images vectorized via Bedrock Titan, embeddings in DynamoDB
- **Phase 4 (AR Web App)**: IN PROGRESS — Local API (FastAPI:3001) + Frontend (Vite:5173) working
- **Phase 5 (Deploy)**: Not started

## Environment
- Python 3.14.3 via uv 0.11.2
- Virtual env: `.venv/`
- Installed: pdfplumber 0.11.9, boto3 1.42.93, scrapy 2.15.0, requests 2.33.1, fastapi 0.136.0, uvicorn 0.45.0
- Git remote: https://github.com/gyovanysantos/jhon-image-reco
- AWS Account: 424009524696, Region: us-east-2
- CDK bootstrapped, 2 stacks deployed: JhonImageRecoStorage, JhonImageRecoScraper

## Local Dev
- API: `uvicorn api.server:app --port 3001` (FastAPI, same logic as Lambda handlers)
- Frontend: `cd frontend && npm run dev -- --port 5173` (Vite proxy → :3001)
- Browser: http://localhost:5173/

## Key Findings
- PDF: `Cat_220_linked_p1.pdf` — 1466 pages, product links begin at page 10
- Annotations have `uri` field that can be `None` — must use `annot.get("uri")` not `.get("uri", "")`
- PDF URLs use `storefront/product-view.ep?pID=` but live site accepts `product-view?pID=` — both work
- Annotation URIs are the most reliable source of part numbers (over regex text scan)
- Product pages return: title, specs (HP, Volts, RPM), brand, mfg #, images at johnstonesupply.sirv.com

## AWS Resources (deployed)
- S3 bucket: `jhon-image-reco-data-424009524696`
  - `csv/parts_catalog.csv` — 100 parts
  - `images/{part_number}/{part_number}_0.jpg` — 100 product images
  - `scraped-data/{part_number}.json` — 100 JSON records
- DynamoDB table: `parts-catalog` — 100 items (each with 1024-dim binary embedding)
- CDK stacks: JhonImageRecoStorage, JhonImageRecoScraper
- OpenSearch: REMOVED (DynamoDB + cosine similarity saves ~$700/month)
- Bedrock: Titan Multimodal Embeddings G1 in us-east-1 (cross-region call from us-east-2)

## Spider Details
- Site blocks unknown user agents (`Disallow: /` for `*` in robots.txt)
- Browser-like User-Agent required for 200 responses
- Product title: `og:title` meta tag
- Brand/Mfg#: `#productBrand`, `#productManufacturerNumber` elements
- Specs: `table.table tr` with `<th>` key + `<td>` value
- Images: `data-productimage` attr → renderImage URL
- renderImage format: `https://www.johnstonesupply.com/images/renderImage?imageName={path}&width=800&height=600`
