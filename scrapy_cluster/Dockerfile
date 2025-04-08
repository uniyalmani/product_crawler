FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir \
    scrapy \
    scrapy-redis \
    kafka-python

CMD ["scrapy", "crawl", "crawl"]
