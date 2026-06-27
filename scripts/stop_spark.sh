#!/bin/bash
# =============================================================
# stop_spark.sh — Stop Spark master + worker only
# Usage: bash scripts/stop_spark.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Stopping Apache Spark"
echo "=================================================="
echo ""

docker-compose -f docker/docker-compose.yml stop spark-master spark-worker
docker-compose -f docker/docker-compose.yml rm -f spark-master spark-worker

echo "✅ Spark stopped"
echo ""
echo "=================================================="
echo "  → Run: bash scripts/start_spark.sh to restart"
echo "=================================================="
echo ""