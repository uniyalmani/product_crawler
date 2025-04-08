import scrapy
from scrapy.exceptions import CloseSpider
import json
from urllib.parse import urlparse, urlunparse
from scrapy.linkextractors import LinkExtractor
from scrapy_redis.spiders import RedisSpider

import redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

def remove_query_params(url):
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query=""))

class ProductSpider(RedisSpider):
    name = 'crawl'
    redis_key = 'crawl-domain'

    def make_request_from_data(self, data):
        try:
            decoded = json.loads(data) if isinstance(data, bytes) else data
            url = decoded.get("url")
            job_id = decoded.get("job_id")

            clean_url = remove_query_params(url)
            self.logger.info(f"📡 Creating request: CLEAN_URL={clean_url}, job_id={job_id}")

            request = scrapy.Request(
                url=clean_url,
                callback=self.parse,
                dont_filter=True  # Avoid duplication issues
            )
            request.meta["job_id"] = job_id  # Add job_id to meta but not as a query param
            return request
        except Exception as e:
            self.logger.error(f" Error parsing Redis data: {data} | {e}")
            return None

    def parse(self, response):
        job_id = response.meta.get("job_id") or "default"
        limit = response.meta.get("limit", 50)
        redis_key = f"result:{job_id}"
        product_patterns = ["/product", "/products", "/p-", "/p/"]

        self.logger.info(f"Parsing: {response.url} for job_id: {job_id}")

        for link in LinkExtractor().extract_links(response):
            if redis_client.llen(redis_key) >= limit:
                self.logger.info(f"Reached limit of {limit} URLs for job_id: {job_id}")
                return

            if any(p in link.url for p in product_patterns):
                redis_client.rpush(redis_key, link.url)
                yield {
                    "url": link.url,
                    "job_id": job_id
                }

            # Crawl the link only if limit not hit
            if redis_client.llen(redis_key) < limit:
                req = scrapy.Request(link.url, callback=self.parse, dont_filter=True)
                req.meta["job_id"] = job_id
                req.meta["limit"] = limit
                yield req

