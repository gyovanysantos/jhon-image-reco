BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Politeness - product pages are public (allowed for Google/Bing in robots.txt)
# but blocked for unknown user agents. We crawl politely with delay.
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 2.5
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# User-Agent — site requires browser-like UA for product pages
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.S3ImagePipeline": 100,
    "scraper.pipelines.S3JsonPipeline": 200,
    "scraper.pipelines.DynamoDBPipeline": 300,
}

# AWS
AWS_REGION = "us-east-2"
S3_BUCKET = "jhon-image-reco-data-424009524696"

# Logging
LOG_LEVEL = "INFO"

# Respect crawl limits
CLOSESPIDER_ITEMCOUNT = 0  # 0 = no limit; set via -a limit=N on CLI

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
