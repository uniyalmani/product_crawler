from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.kafka_producer import send_crawl_request
from app.crawler import Crawler
import uuid
import redis

from app.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)


logger.info("FastAPI is starting...")

app = FastAPI()

class CrawlRequest(BaseModel):
    domains: List[str]



@app.post("/crawl")
async def crawl_domains(request: CrawlRequest):
    try:
        job_id = str(uuid.uuid4())  # unique job ID
        for domain in request.domains:
            send_crawl_request(domain, job_id)
        return {"status": "submitted", "job_id": job_id, "domains": request.domains}
    except Exception as e:
        logger.error(f"Error while crawling: {e}")
        raise HTTPException(status_code=500, detail=str(e))






@app.post("/local-crawl")
async def local_crawl(request: CrawlRequest):
    crawler = Crawler(request.domains)
    result = await crawler.run()
    return result




redis_client = redis.Redis(host='redis', port=6379, db=0)

@app.get("/result/{job_id}")
def get_result(job_id: str):
    results = redis_client.lrange(f"result:{job_id}", 0, -1)
    return {"job_id": job_id, "urls": [r.decode() for r in results]}