#!/bin/bash
# =============================================================
# step06.sh — Run dbt Gold layer transformations
# Reads from Silver → writes to Gold (Parquet via dbt)
# Usage: bash scripts/step06.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 06 — dbt Gold Layer"
echo "  Silver (Iceberg) → Gold (Parquet/dbt)"
echo "=================================================="
echo ""

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# ── Check Java 17 ──────────────────────────────────────────
java -version 2>&1 | grep "17" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Java 17 not active — please run:"
    echo "   export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64"
    echo "   export PATH=\$JAVA_HOME/bin:\$PATH"
    exit 1
fi
echo "✅ Java 17 active"
echo ""

# ── Run dbt ────────────────────────────────────────────────
echo "🏗️  Running dbt models..."
cd dbt/f1_gold
dbt run --full-refresh

echo ""
echo "🧪 Running dbt tests..."
dbt test

echo ""
echo "=================================================="
echo "  ✅ Step 06 Complete!"
echo ""
echo "  Gold tables location:"
echo "  dbt/f1_gold/spark-warehouse/gold_gold.db/"
echo ""
echo "  Next step → bash scripts/step07.sh"
echo "=================================================="
echo ""
