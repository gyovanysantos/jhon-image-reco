"""
Phase 2: Scrapy spider for Johnstone Supply product pages.

Reads part numbers from CSV, scrapes each product page for details and images.
"""

import csv
import io
from pathlib import Path

import boto3
import scrapy

from scraper.items import PartItem


class JohnstoneSpider(scrapy.Spider):
    name = "johnstone"
    allowed_domains = ["johnstonesupply.com", "johnstonesupply.sirv.com"]

    def __init__(self, csv_source="local", limit=None, *args, **kwargs):
        """
        Args:
            csv_source: "local" to read from output/parts_catalog.csv,
                        "s3" to read from S3 bucket.
            limit: Max number of parts to scrape (None = all).
        """
        super().__init__(*args, **kwargs)
        self.csv_source = csv_source
        self.limit = int(limit) if limit else None

    def start_requests(self):
        parts = self._load_csv()
        for i, row in enumerate(parts):
            if self.limit and i >= self.limit:
                break
            yield scrapy.Request(
                url=row["url"],
                callback=self.parse_product,
                meta={
                    "part_number": row["part_number"],
                    "catalog_page": row.get("catalog_page", ""),
                    "csv_description": row.get("description", ""),
                },
            )

    def _load_csv(self) -> list[dict]:
        if self.csv_source == "s3":
            s3 = boto3.client("s3")
            obj = s3.get_object(
                Bucket="jhon-image-reco-data-424009524696", Key="csv/parts_catalog.csv"
            )
            text = obj["Body"].read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)
        else:
            csv_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "output"
                / "parts_catalog.csv"
            )
            with open(csv_path, encoding="utf-8") as f:
                return list(csv.DictReader(f))

    def parse_product(self, response):
        part_number = response.meta["part_number"]

        # Title — from og:title meta tag (most reliable) or [class*=Spec] container
        title = response.css('meta[property="og:title"]::attr(content)').get("").strip()
        if not title:
            title = response.css('[class*="Spec"]::text').getall()
            title = " ".join(t.strip() for t in title if t.strip())

        # Order #, Mfg #, Brand — from dedicated <strong> elements
        mfg_number = response.css("#productManufacturerNumber::text").get("").strip()
        brand = response.css("#productBrand::text").get("").strip()

        # Specifications table — uses <th> for keys and <td> for values
        specs = {}
        spec_rows = response.css("table.table tr")
        for row in spec_rows:
            key = row.css("th::text").get("").strip()
            value = row.css("td::text").get("").strip()
            if key and value:
                specs[key] = value

        # Description — from CSV fallback (page description is usually the title)
        description = response.meta.get("csv_description", "")

        # Catalog page
        catalog_page = response.meta.get("catalog_page", "")

        # Images — product images via renderImage endpoint and Sirv CDN
        image_urls = []
        seen = set()
        RENDER_BASE = "https://www.johnstonesupply.com/images/renderImage"

        # Primary: Sirv viewer div contains the image path for renderImage
        # e.g. data-productimage="WEB/10097/N99-394cl.jpg"
        for path in response.css('.Sirv::attr(data-productimage)').getall():
            url = f"{RENDER_BASE}?imageName={path}&width=800&height=600"
            if url not in seen:
                seen.add(url)
                image_urls.append(url)

        # Sirv CDN thumbnails (loaded via JS, may not always be in HTML)
        for url in response.css('img[src*="johnstonesupply.sirv.com"]::attr(src)').getall():
            clean = url.split("?")[0]
            if clean not in seen:
                seen.add(clean)
                image_urls.append(clean)

        # renderImage URLs directly in img tags
        for url in response.css('img[src*="renderImage"]::attr(src)').getall():
            if url.startswith("/"):
                url = f"https://www.johnstonesupply.com{url}"
            if url not in seen:
                seen.add(url)
                image_urls.append(url)

        # Datasheets and resources
        datasheets = []
        resource_links = response.css('a[href*=".pdf"], a[href*="youtube"], a[href*="catalog"]')
        for link in resource_links:
            href = link.attrib.get("href", "")
            text = link.css("::text").get("").strip()
            if href:
                datasheets.append({"title": text, "url": href})

        item = PartItem()
        item["part_number"] = part_number
        item["title"] = title
        item["description"] = description
        item["brand"] = brand
        item["mfg_number"] = mfg_number
        item["catalog_page"] = catalog_page
        item["url"] = response.url
        item["specifications"] = specs
        item["image_urls"] = image_urls
        item["image_keys"] = []  # Populated by S3ImagePipeline
        item["datasheets"] = datasheets
        item["pricing"] = "Sign in required"

        yield item
