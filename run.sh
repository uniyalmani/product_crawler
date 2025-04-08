#!/bin/bash

echo "📦 Loading environment from .env"
export $(grep -v '^#' .env | xargs)

echo "🐳 Building and starting containers..."
docker-compose up --build
