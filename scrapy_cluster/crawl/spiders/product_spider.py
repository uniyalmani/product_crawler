import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy_redis.spiders import RedisSpider

class ProductSpider(RedisSpider):
    name = 'crawl'
    redis_key = 'crawl-domain'

    def parse(self, response):
        job_id = response.meta.get("job_id")  # pass through metadata

        product_patterns = ["/product", "/products", "/p-", "/p/"]
        for link in LinkExtractor().extract_links(response):
            if any(p in link.url for p in product_patterns):
                yield {
                    "url": link.url,
                    "job_id": job_id
                }

            yield scrapy.Request(link.url, callback=self.parse, meta={"job_id": job_id})
