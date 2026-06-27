#!/bin/bash
# =============================================================
# step05.sh — Run Bronze → Silver PySpark transformations
# Reads from MinIO Bronze → writes to MinIO Silver (Iceberg)
# Usage: bash scripts/step05.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 05 — PySpark Silver Layer"
echo "  Bronze (raw CSV) → Silver (clean Iceberg/Parquet)"
echo "=================================================="
echo ""

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

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

# ── Check Bronze data exists ───────────────────────────────
python3 -c "
import boto3
from botocore.client import Config
c = boto3.client('s3', endpoint_url='http://localhost:9000',
    aws_access_key_id='f1minio', aws_secret_access_key='f1minio123',
    config=Config(signature_version='s3v4'), region_name='us-east-1')
r = c.list_objects_v2(Bucket='f1-bronze')
count = len(r.get('Contents', []))
if count == 0:
    print('❌ Bronze layer is empty — run step04.sh first')
    exit(1)
print(f'✅ Bronze layer has {count} objects')
" 2>/dev/null
echo ""

# ── Run Silver transformations ─────────────────────────────
echo "⚡ Running PySpark Silver transformations..."
echo "   (This will take 5-10 minutes)"
echo ""
python -m processing.silver.run_all_silver

echo ""
echo "=================================================="
echo "  ✅ Step 05 Complete!"
echo ""
echo "  🪣 Silver tables in MinIO:"
echo "     → Open port 9001 to browse f1-silver bucket"
echo ""
echo "  Next step → bash scripts/step06.sh (dbt Gold layer)"
echo "=================================================="
echo ""
