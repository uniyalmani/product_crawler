from kafka import KafkaConsumer
import redis
import json
import os
from dotenv import load_dotenv
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)



# Load env variables
load_dotenv()

KAFKA_TOPIC = os.getenv("KAFKA_RESULT_TOPIC", "crawl-items")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVERS,
    group_id='crawler-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest'
)

# Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

print(f"Listening to Kafka topic '{KAFKA_TOPIC}' and saving results to Redis...")

# Consume messages
for message in consumer:
    data = message.value
    url = data.get("url")
    job_id = data.get("job_id")
    
    if url and job_id:
        logger.info(f"Received item: {url} for job_id: {job_id}")
        # Save under Redis list with job ID
        redis_client.rpush(f"result:{job_id}", url)
