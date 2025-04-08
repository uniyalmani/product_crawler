from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable, KafkaError
import redis
import json
import os
import time
from dotenv import load_dotenv
import socket
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("kafka_to_redis_bridge")

load_dotenv()

def wait_for_network_service(host, port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    return False

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crawl-domain")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_QUEUE = KAFKA_TOPIC

MAX_RETRIES = 30  # Increased retries
RETRY_DELAY = 5

# First wait for network availability
logger.info(f"⏳ Waiting for Kafka network availability at {KAFKA_SERVERS}...")
if not wait_for_network_service("kafka", 9092, timeout=60):
    raise Exception(" Kafka network not reachable after timeout")

consumer = None
for attempt in range(1, MAX_RETRIES + 1):
    try:
        logger.info(f"⏳ Attempting Kafka connection... (Try {attempt}/{MAX_RETRIES})")
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
            auto_offset_reset='earliest',
            group_id='bridge-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            api_version=(2, 0, 2)  # Explicit API version
        )
        # Test the connection
        consumer.topics()
        logger.info("Connected to Kafka.")
        break
    except (NoBrokersAvailable, KafkaError) as e:
        logger.info(f" Kafka connection failed: {str(e)}. Retrying...")
        time.sleep(RETRY_DELAY)
    except Exception as e:
        logger.info(f" Unexpected error: {str(e)}")
        time.sleep(RETRY_DELAY)

if not consumer:
    raise Exception(" Kafka not reachable after multiple retries.")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

logger.info(f" Kafka → Redis bridge started for topic '{KAFKA_TOPIC}'")
logger.info(" Waiting for Kafka messages...")

try:
    for message in consumer:
        try:
            value = message.value
            url = value.get("url")
            job_id = value.get("job_id")
            limit = value.get("limit", 50)
            logger.info(f"🔄 Bridging to Redis: {url}")

            redis_client.lpush(REDIS_QUEUE, json.dumps({
                "url": url,
                "job_id": job_id,
                "limit": limit
            }))
        except Exception as e:
            logger.info(f"⚠️ Error processing message: {str(e)}")
except KeyboardInterrupt:
    logger.info("Shutting down...")
finally:
    consumer.close()