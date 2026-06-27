#!/bin/bash
# =============================================================
# start_spark.sh — Start Spark master + worker only
# Usage: bash scripts/start_spark.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Starting Apache Spark"
echo "=================================================="
echo ""

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "⚡ Starting Spark Master + Worker..."
docker-compose -f docker/docker-compose.yml up -d spark-master spark-worker

echo "⏳ Waiting for Spark to be ready..."
sleep 5

docker ps | grep f1_spark_master > /dev/null 2>&1 \
    && echo "✅ Spark Master running (port 7077)" \
    || echo "⚠️  Spark Master not ready yet"

docker ps | grep f1_spark_worker > /dev/null 2>&1 \
    && echo "✅ Spark Worker running" \
    || echo "⚠️  Spark Worker not ready yet"

echo ""
echo "=================================================="
echo "  ⚡ Spark Master UI → Open port 8082 in Ports tab"
echo "  ⚡ Spark Connect   → spark://localhost:7077"
echo "=================================================="
echo ""