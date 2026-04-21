BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Politeness
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2.5
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# User-Agent
USER_AGENT = "JhonImageReco Bot/1.0 (+https://github.com/gyovanysantos/jhon-image-reco)"

# Pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.S3ImagePipeline": 100,
    "scraper.pipelines.S3JsonPipeline": 200,
    "scraper.pipelines.DynamoDBPipeline": 300,
}

# AWS
AWS_REGION = "us-east-1"
S3_BUCKET = "jhon-image-reco-data"

# Logging
LOG_LEVEL = "INFO"

# Respect crawl limits
CLOSESPIDER_ITEMCOUNT = 0  # 0 = no limit; set via -a limit=N on CLI

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
