"""
Phase 2: Scrapy pipelines for S3 image upload, S3 JSON storage, and DynamoDB writes.
"""

import json
import hashlib
from io import BytesIO

import boto3
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from itemadapter import ItemAdapter


class S3ImagePipeline:
    """Download product images and upload them to S3."""

    def __init__(self, bucket_name, region):
        self.bucket_name = bucket_name
        self.region = region

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            bucket_name=crawler.settings.get("S3_BUCKET", "jhon-image-reco-data"),
            region=crawler.settings.get("AWS_REGION", "us-east-1"),
        )

    def open_spider(self, spider):
        self.s3 = boto3.client("s3", region_name=self.region)
        self.http_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/*,*/*;q=0.8",
        }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        image_urls = adapter.get("image_urls", [])
        part_number = adapter["part_number"]
        image_keys = []

        for i, url in enumerate(image_urls):
            try:
                import requests as req_lib
                response = req_lib.get(url, headers=self.http_headers, timeout=30)
                response.raise_for_status()

                # Determine extension
                content_type = response.headers.get("content-type", "image/jpeg")
                ext = "jpg"
                if "png" in content_type:
                    ext = "png"
                elif "webp" in content_type:
                    ext = "webp"

                s3_key = f"images/{part_number}/{part_number}_{i}.{ext}"
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=response.content,
                    ContentType=content_type,
                )
                image_keys.append(s3_key)
                spider.logger.info(f"Uploaded image to s3://{self.bucket_name}/{s3_key}")
            except Exception as e:
                spider.logger.error(f"Failed to download image {url}: {e}")

        adapter["image_keys"] = image_keys
        return item


class S3JsonPipeline:
    """Store scraped item data as JSON in S3."""

    def __init__(self, bucket_name, region):
        self.bucket_name = bucket_name
        self.region = region

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            bucket_name=crawler.settings.get("S3_BUCKET", "jhon-image-reco-data"),
            region=crawler.settings.get("AWS_REGION", "us-east-1"),
        )

    def open_spider(self, spider):
        self.s3 = boto3.client("s3", region_name=self.region)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        part_number = adapter["part_number"]
        data = dict(adapter)

        s3_key = f"scraped-data/{part_number}.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(data, indent=2, default=str),
            ContentType="application/json",
        )
        spider.logger.info(f"Stored JSON to s3://{self.bucket_name}/{s3_key}")
        return item


class DynamoDBPipeline:
    """Write scraped item data to DynamoDB."""

    def __init__(self, region, table_name):
        self.region = region
        self.table_name = table_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            region=crawler.settings.get("AWS_REGION", "us-east-1"),
            table_name="parts-catalog",
        )

    def open_spider(self, spider):
        dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = dynamodb.Table(self.table_name)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        db_item = {
            "part_number": adapter["part_number"],
            "title": adapter.get("title", ""),
            "description": adapter.get("description", ""),
            "brand": adapter.get("brand", ""),
            "mfg_number": adapter.get("mfg_number", ""),
            "catalog_page": str(adapter.get("catalog_page", "")),
            "url": adapter.get("url", ""),
            "specifications": adapter.get("specifications", {}),
            "image_keys": adapter.get("image_keys", []),
            "datasheets": [
                {"title": d.get("title", ""), "url": d.get("url", "")}
                for d in adapter.get("datasheets", [])
            ],
            "pricing": adapter.get("pricing", "Sign in required"),
        }

        # DynamoDB doesn't allow empty strings for non-key attributes in some cases
        db_item = {k: v for k, v in db_item.items() if v != "" and v != [] and v != {}}
        db_item["part_number"] = adapter["part_number"]  # Always include PK

        self.table.put_item(Item=db_item)
        spider.logger.info(f"Wrote {adapter['part_number']} to DynamoDB")
        return item
