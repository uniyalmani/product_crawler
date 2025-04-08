BOT_NAME = 'crawl'

SPIDER_MODULES = ['crawl.spiders']
NEWSPIDER_MODULE = 'crawl.spiders'

# Kafka + Redis
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER_PERSIST = True

REDIS_HOST = 'redis'
REDIS_PORT = 6379

# Optional: push crawled data to Kafka (requires custom pipeline)
# ITEM_PIPELINES = {
#     'crawl.pipelines.KafkaPipeline': 100,
# }

DOWNLOAD_DELAY = 0.5  # Be nice
ROBOTSTXT_OBEY = False
