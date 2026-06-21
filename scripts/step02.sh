#!/bin/bash
# =============================================================
# step02.sh — Load F1 data into PostgreSQL Star Schema DWH
# Reads from data/raw/ CSVs → loads into PostgreSQL
# Usage: bash scripts/step02.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 02 — Load PostgreSQL Data Warehouse"
echo "  Target: Star Schema (5 dims + 4 facts)"
echo "=================================================="
echo ""

# ── Check PostgreSQL is running ────────────────────────────
echo "🔍 Checking PostgreSQL connection..."
docker exec f1_postgres pg_isready -U f1user -d f1_warehouse > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ PostgreSQL is not running!"
    echo "   Run: bash scripts/start.sh first"
    exit 1
fi
echo "✅ PostgreSQL is ready"
echo ""

# ── Check raw data exists ──────────────────────────────────
if [ ! -f "data/raw/results.csv" ]; then
    echo "❌ Raw data not found in data/raw/"
    echo "   Run: bash scripts/step01.sh first"
    exit 1
fi
echo "✅ Raw data found in data/raw/"
echo ""

# ── Recreate schema ────────────────────────────────────────
echo "🏗️  Recreating Star Schema tables..."
docker exec -i f1_postgres psql -U f1user -d f1_warehouse < warehouse/schema.sql > /dev/null
echo "✅ Schema ready"
echo ""

# ── Load warehouse ─────────────────────────────────────────
echo "📥 Loading data into warehouse..."
echo ""
python -m warehouse.load_warehouse

echo ""
echo "=================================================="
echo "  ✅ Step 02 Complete!"
echo ""
echo "  Next step → bash scripts/step03.sh"
echo "=================================================="
echo ""