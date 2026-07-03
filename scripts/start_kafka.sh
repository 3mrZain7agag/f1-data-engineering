#!/bin/bash
# =============================================================
# start_kafka.sh — Start Kafka + Zookeeper + Kafka UI only
# Usage: bash scripts/start_kafka.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Starting Kafka Stack"
echo "=================================================="
echo ""

echo "📨 Starting Zookeeper + Kafka + Kafka UI..."
docker-compose -f docker/docker-compose.yml up -d zookeeper kafka kafka-ui

echo "⏳ Waiting for Kafka to be ready..."
sleep 10

docker exec f1_kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1 \
    && echo "✅ Kafka is ready" \
    || echo "⚠️  Kafka not ready yet — wait a few more seconds"

echo ""
echo "=================================================="
echo "  📨 Kafka         → localhost:9092"
echo "  🌐 Kafka UI      → Open port 8085 in Ports tab"
echo "=================================================="
echo ""