#!/bin/bash
# =============================================================
# stop_kafka.sh — Stop Kafka + Zookeeper + Kafka UI only
# Usage: bash scripts/stop_kafka.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Stopping Kafka Stack"
echo "=================================================="
echo ""

# Stop any running streaming consumer first
if [ -f /tmp/f1_consumer.pid ]; then
    kill "$(cat /tmp/f1_consumer.pid)" 2>/dev/null && echo "✅ Streaming consumer stopped"
    rm -f /tmp/f1_consumer.pid
fi

docker-compose -f docker/docker-compose.yml stop kafka zookeeper kafka-ui
docker-compose -f docker/docker-compose.yml rm -f kafka zookeeper kafka-ui

echo "✅ Kafka stack stopped"
echo ""
echo "=================================================="
echo "  → Run: bash scripts/start_kafka.sh to restart"
echo "=================================================="
echo ""