# kafka_to_redis_bridge.py
from kafka import KafkaConsumer
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crawl-domain")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_QUEUE = KAFKA_TOPIC  # Use same name for Redis queue

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVERS,
    auto_offset_reset='earliest',
    group_id='bridge-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

print(f"Kafka → Redis bridge listening on topic '{KAFKA_TOPIC}' and pushing to Redis queue '{REDIS_QUEUE}'...")

for message in consumer:
    value = message.value
    print(f"🔄 Bridging: {value}")
    redis_client.lpush(REDIS_QUEUE, json.dumps(value))
