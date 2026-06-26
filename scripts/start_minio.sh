#!/bin/bash
# =============================================================
# start_minio.sh — Start MinIO only
# Usage: bash scripts/start_minio.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Starting MinIO"
echo "=================================================="
echo ""

echo "🪣 Starting MinIO container..."
docker-compose -f docker/docker-compose.yml up -d minio

echo "⏳ Waiting for MinIO to be ready..."
sleep 3

curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1 \
    && echo "✅ MinIO is ready" \
    || echo "⚠️  MinIO not ready yet — wait a few seconds"

echo ""
echo "=================================================="
echo "  🪣 MinIO API → localhost:9000"
echo "  🌐 MinIO UI  → Open port 9001 in Ports tab"
echo "  🔑 Login     → f1minio / f1minio123"
echo "=================================================="
echo ""