FROM python:3.11-slim
WORKDIR /app
COPY kafka_to_redis_bridge.py .
RUN pip install kafka-python redis python-dotenv
CMD ["python", "kafka_to_redis_bridge.py"]
