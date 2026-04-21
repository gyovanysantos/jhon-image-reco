import scrapy


class PartItem(scrapy.Item):
    """Structured item for a Johnstone Supply HVAC part."""

    part_number = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    brand = scrapy.Field()
    mfg_number = scrapy.Field()
    catalog_page = scrapy.Field()
    url = scrapy.Field()
    specifications = scrapy.Field()
    image_urls = scrapy.Field()
    image_keys = scrapy.Field()
    datasheets = scrapy.Field()
    pricing = scrapy.Field()
