# Product Crawler

A scalable e-commerce crawler that collects product URLs from domains using Kafka, Redis, Scrapy, and FastAPI.

## Features

Accepts crawl requests via API with custom limits

Distributed architecture using Kafka & Redis

Async Scrapy spider that auto-terminates on reaching the crawl limit

Real-time result access via API

Architecture

flowchart TD
```
    A[API Request] --> B[FastAPI Server]
    B --> C[Kafka Topic: crawl-domain]
    C --> D[Kafka to Redis Bridge]
    D --> E[Redis Queue: crawl-domain]
    E --> F[Scrapy Spider (RedisSpider)]
    F --> G[Result Stored in Redis as result:<job_id>]
    G --> H[API: Get Results]

```

## How to Run
1. Clone the Repository
```
git clone https://github.com/uniyalmani/product_crawler.git
cd product_crawler
```
2. Create .env file
```
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=crawl-domain
REDIS_HOST=redis
REDIS_PORT=6379
```
3. Start with Docker
```
docker-compose up --build
```
This will start the following containers:

    redis: For job queue and results storage

    zookeeper & kafka: Messaging system

    kafka_to_redis_bridge: Bridges Kafka to Redis

    scrapy_worker: Scrapy spider reading from Redis

    fastapi: API server (docs available at http://localhost:8000/docs)

## API Usage
1. Crawl a Domain

POST /crawl
```
{
  "domains": ["https://www.westside.com"]
}
```
You can optionally add limit per domain (default: 50):
```
{
  "domains": ["https://www.westside.com"],
  "limit": 100
}
```
Response:
```
{
  "status": "submitted",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "domains": ["https://www.westside.com"]
}
```
2. Get Results for Specific Job

GET /result/{job_id}

Example:

GET /result/123e4567-e89b-12d3-a456-426614174000

Response:
```
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "urls": [
    "https://www.westside.com/products/item-1",
    "https://www.westside.com/products/item-2"
  ]
}
```
3. Get All Results

GET /result

Response:
```
{
  "total_jobs": 2,
  "results": [
    {
      "job_id": "job-id-1",
      "urls": [...]
    },
    {
      "job_id": "job-id-2",
      "urls": [...]
    }
  ]
}
```

## API Documentation

FastAPI automatically provides interactive documentation at the following endpoints:

    Swagger UI:
    http://localhost:8000/docs

    ReDoc (alternative style):
    http://localhost:8000/redoc

You can test all endpoints directly from these pages in your browser.

Tech Stack

    Python 3.11

    Scrapy + scrapy-redis

    FastAPI

    Kafka (Confluent)

    Redis

    Docker + Docker Compose
