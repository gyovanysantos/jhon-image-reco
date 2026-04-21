# Project Memory

## Current State
- **Phase 1 (PDF Extraction)**: COMPLETE — 100 parts extracted to `output/parts_catalog.csv`
- **Phase 2 (Scraping)**: Not started
- **Phase 3 (Vectorization)**: Not started
- **Phase 4 (AR Web App)**: Not started
- **Phase 5 (Deploy)**: Not started

## Environment
- Python 3.14.3 via uv 0.11.2
- Virtual env: `.venv/`
- Installed: pdfplumber 0.11.9, boto3 1.42.93
- Git remote: https://github.com/gyovanysantos/jhon-image-reco

## Key Findings
- PDF: `Cat_220_linked_p1.pdf` — 1466 pages, product links begin at page 10
- Annotations have `uri` field that can be `None` — must use `annot.get("uri")` not `.get("uri", "")`
- PDF URLs use `storefront/product-view.ep?pID=` but live site accepts `product-view?pID=` — both work
- Annotation URIs are the most reliable source of part numbers (over regex text scan)
- Product pages return: title, specs (HP, Volts, RPM), brand, mfg #, images at johnstonesupply.sirv.com

## AWS Resources (to be created)
- S3 bucket: `jhon-image-reco-data`
- DynamoDB table: `jhon-image-reco-parts`
- OpenSearch collection: `jhon-image-reco-vectors`
