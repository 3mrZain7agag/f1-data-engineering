#!/bin/bash
# =============================================================
# step04.sh — Upload raw F1 data to Bronze Data Lake (MinIO)
# Reads from data/raw/ → uploads to s3://f1-bronze/
# Usage: bash scripts/step04.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 04 — Bronze Data Lake Ingestion"
echo "  Target: MinIO → s3://f1-bronze/"
echo "=================================================="
echo ""

# ── Check MinIO is running ─────────────────────────────────
echo "🔍 Checking MinIO connection..."
curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ MinIO is not running!"
    echo "   Run: bash scripts/start.sh first"
    exit 1
fi
echo "✅ MinIO is ready"
echo ""

# ── Check raw data exists ──────────────────────────────────
if [ ! -f "data/raw/results.csv" ]; then
    echo "❌ Raw data not found in data/raw/"
    echo "   Run: bash scripts/step01.sh first"
    exit 1
fi
echo "✅ Raw data found in data/raw/"
echo ""

# ── Upload to Bronze ───────────────────────────────────────
echo "📤 Uploading to Bronze layer..."
echo ""
python -m datalake.bronze.ingest_to_bronze

echo ""
echo "=================================================="
echo "  ✅ Step 04 Complete!"
echo ""
echo "  🪣 MinIO UI → Open port 9001 in Ports tab"
echo "  🔑 Login    → f1minio / f1minio123"
echo "  📁 Bucket   → f1-bronze"
echo ""
echo "  Next step → bash scripts/step05.sh"
echo "=================================================="
echo ""