# app/kafka_producer.py
from kafka import KafkaProducer
import json, os
from dotenv import load_dotenv
from app.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crawl-domain")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_crawl_request(domain: str, job_id: str):
    logger.info(f"Received product domain: {domain} for job_id: {job_id}")
    producer.send(KAFKA_TOPIC, {
        "url": f"https://{domain}",
        "spider": "crawl",
        "dont_filter": True,
        "job_id": job_id
    })
    producer.flush()
