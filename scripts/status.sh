#!/bin/bash
# =============================================================
# status.sh — Check status of all services
# Usage: bash scripts/status.sh
# =============================================================

echo ""
echo "=================================================="
echo "  F1 Data Engineering — Service Status"
echo "=================================================="
echo ""

# ── PostgreSQL ─────────────────────────────────────────────
docker exec f1_postgres pg_isready -U f1user -d f1_warehouse > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  🐳 PostgreSQL    → ✅ Running (port 5432)"
else
    echo "  🐳 PostgreSQL    → ❌ Not running"
fi

# ── MinIO ──────────────────────────────────────────────────
curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  🪣 MinIO API     → ✅ Running (port 9000)"
    echo "  🌐 MinIO UI      → ✅ Running (port 9001)"
else
    echo "  🪣 MinIO         → ❌ Not running"
fi

# ── Spark ──────────────────────────────────────────────────
docker ps | grep f1_spark_master > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ⚡ Spark Master  → ✅ Running (port 7077, UI: 8082)"
else
    echo "  ⚡ Spark Master  → ❌ Not running"
fi

docker ps | grep f1_spark_worker > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ⚡ Spark Worker  → ✅ Running"
else
    echo "  ⚡ Spark Worker  → ❌ Not running"
fi

# ── Airflow Webserver ──────────────────────────────────────
curl -s http://localhost:8080/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✈️  Airflow UI    → ✅ Running (port 8080)"
else
    echo "  ✈️  Airflow UI    → ❌ Not running"
fi

# ── Airflow Scheduler ──────────────────────────────────────
pgrep -f "airflow scheduler" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ⏰ Scheduler     → ✅ Running"
else
    echo "  ⏰ Scheduler     → ❌ Not running"
fi

# ── Data Summary ───────────────────────────────────────────
echo ""
echo "  📊 Data Summary:"

# Check raw data
if [ -f "data/raw/results.csv" ]; then
    RESULTS=$(wc -l < data/raw/results.csv)
    echo "     data/raw/      → ✅ $(($RESULTS - 1)) results rows"
else
    echo "     data/raw/      → ❌ No data (run step01.sh)"
fi

# Check PostgreSQL data
docker exec f1_postgres pg_isready -U f1user > /dev/null 2>&1
if [ $? -eq 0 ]; then
    COUNT=$(docker exec f1_postgres psql -U f1user -d f1_warehouse -t -c "SELECT COUNT(*) FROM fact_race_results;" 2>/dev/null | tr -d ' ')
    if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ] 2>/dev/null; then
        echo "     PostgreSQL DWH → ✅ $COUNT race results"
    else
        echo "     PostgreSQL DWH → ❌ Empty (run step02.sh)"
    fi
fi

# Check MinIO Bronze
curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1
if [ $? -eq 0 ]; then
    BRONZE=$(python3 -c "
import boto3
from botocore.client import Config
try:
    c = boto3.client('s3', endpoint_url='http://localhost:9000',
        aws_access_key_id='f1minio', aws_secret_access_key='f1minio123',
        config=Config(signature_version='s3v4'), region_name='us-east-1')
    r = c.list_objects_v2(Bucket='f1-bronze')
    print(len(r.get('Contents', [])))
except:
    print(0)
" 2>/dev/null)
    if [ "$BRONZE" -gt 0 ] 2>/dev/null; then
        echo "     MinIO Bronze   → ✅ $BRONZE objects in f1-bronze"
    else
        echo "     MinIO Bronze   → ❌ Empty (run step04.sh)"
    fi

    # Check MinIO Silver
    SILVER=$(python3 -c "
import boto3
from botocore.client import Config
try:
    c = boto3.client('s3', endpoint_url='http://localhost:9000',
        aws_access_key_id='f1minio', aws_secret_access_key='f1minio123',
        config=Config(signature_version='s3v4'), region_name='us-east-1')
    r = c.list_objects_v2(Bucket='f1-silver')
    print(len(r.get('Contents', [])))
except:
    print(0)
" 2>/dev/null)
    if [ "$SILVER" -gt 0 ] 2>/dev/null; then
        echo "     MinIO Silver   → ✅ $SILVER objects in f1-silver"
    else
        echo "     MinIO Silver   → ❌ Empty (run step05.sh)"
    fi
fi

# Check dbt Gold (local warehouse)
if [ -d "dbt/f1_gold/spark-warehouse/gold_gold.db" ]; then
    GOLD_COUNT=$(ls dbt/f1_gold/spark-warehouse/gold_gold.db 2>/dev/null | wc -l)
    echo "     dbt Gold       → ✅ $GOLD_COUNT tables (local)"
else
    echo "     dbt Gold       → ❌ Not built (run step06.sh)"
fi

echo ""
echo "=================================================="
echo "  📋 Quick Commands:"
echo "  → bash scripts/start.sh          Start everything"
echo "  → bash scripts/start_postgres.sh Start PostgreSQL only"
echo "  → bash scripts/start_minio.sh    Start MinIO only"
echo "  → bash scripts/start_airflow.sh  Start Airflow only"
echo "  → bash scripts/start_spark.sh    Start Spark only"
echo ""
echo "  → bash scripts/stop.sh           Stop everything"
echo "  → bash scripts/stop_postgres.sh  Stop PostgreSQL only"
echo "  → bash scripts/stop_minio.sh     Stop MinIO only"
echo "  → bash scripts/stop_airflow.sh   Stop Airflow only"
echo "  → bash scripts/stop_spark.sh     Stop Spark only"
echo ""
echo "  → bash scripts/stepXX.sh         Run Step XX (e.g. step01.sh, step02.sh)"
echo "  → bash scripts/steps.sh          Show full steps dictionary"
echo "=================================================="
echo ""