#!/bin/bash
# =============================================================
# stop_minio.sh — Stop MinIO only
# Usage: bash scripts/stop_minio.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Stopping MinIO"
echo "=================================================="
echo ""

docker-compose -f docker/docker-compose.yml stop minio
docker-compose -f docker/docker-compose.yml rm -f minio

echo "✅ MinIO stopped"
echo ""