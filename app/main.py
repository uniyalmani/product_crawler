from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,Field
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
    limit: int = Field(default=50, ge=1, description="Maximum number of product URLs to crawl per domain")



@app.post("/crawl")
async def crawl_domains(request: CrawlRequest):
    try:
        job_id = str(uuid.uuid4())
        for domain in request.domains:
            send_crawl_request(domain, job_id, request.limit)
        return {"status": "submitted", "job_id": job_id, "domains": request.domains, "limit": request.limit}
    except Exception as e:
        logger.error(f"Error while crawling: {e}")
        raise HTTPException(status_code=500, detail=str(e))






@app.post("/local-crawl")
async def local_crawl(request: CrawlRequest):
    crawler = Crawler(request.domains)
    result = await crawler.run()
    return result




redis_client = redis.Redis(host='redis', port=6379, db=0)


@app.get("/result")
def get_all_results():
    keys = redis_client.keys("result:*")
    if not keys:
        return {"message": "No results found.", "results": []}

    all_results = []

    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        job_id = key_str.replace("result:", "")
        urls = redis_client.lrange(key, 0, -1)
        all_results.append({
            "job_id": job_id,
            "urls": [u.decode() for u in urls]
        })

    return {
        "total_jobs": len(all_results),
        "results": all_results
    }

@app.get("/result/{job_id}")
def get_result(job_id: str):
    redis_key = f"result:{job_id}"
    results = redis_client.lrange(redis_key, 0, -1)

    if not results:
        logger.warning(f"No results found for job_id: {job_id}")
        raise HTTPException(status_code=404, detail=f"No results found for job_id: {job_id}")

    decoded_urls = []
    for r in results:
        try:
            decoded_urls.append(r.decode())
        except Exception as e:
            logger.error(f"Failed to decode result for job_id={job_id}: {str(e)}")
            continue

    logger.info(f"Fetched {len(decoded_urls)} URLs for job_id: {job_id}")
    return {
        "job_id": job_id,
        "urls": decoded_urls
    }