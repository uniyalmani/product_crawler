from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json, os, time
from dotenv import load_dotenv
from app.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crawl-domain")
logger.info('KAFKA_SERVERS: ' + KAFKA_SERVERS)
MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds

# Retry connecting to Kafka
producer = None
for attempt in range(1, MAX_RETRIES + 1):
    try:
        logger.info(f"Attempting to connect to Kafka (Attempt {attempt})...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        logger.info("✅ Connected to Kafka.")
        break
    except NoBrokersAvailable:
        logger.warning(f"⚠️ Kafka not available. Retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)

if not producer:
    logger.error("Kafka not available after multiple retries.")
    raise Exception("Kafka not available after retries")

from urllib.parse import urlparse
def normalize_domain(domain: str) -> str:
    # Remove scheme if present
    parsed = urlparse(domain)
    return parsed.netloc or domain

def send_crawl_request(domain: str, job_id: str, limit: int = 50):
    normalized = normalize_domain(domain)
    full_url = f"https://{normalized}"
    logger.info(f"Sending to Kafka: {full_url} for job {job_id} with limit {limit}")

    producer.send(KAFKA_TOPIC, {
        "url": full_url,
        "job_id": job_id,
        "limit": limit
    })
    producer.flush()