#!/bin/bash
# =============================================================
# step03.sh — Trigger Airflow DAGs for F1 pipeline
# Triggers ingestion DAG then warehouse load DAG
# Usage: bash scripts/step03.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 03 — Apache Airflow Orchestration"
echo "=================================================="
echo ""

export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow

# ── Check Airflow is running ───────────────────────────────
echo "🔍 Checking Airflow status..."
airflow jobs check 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Airflow may not be running."
    echo "   Run: bash scripts/start.sh first"
    echo ""
fi

# ── Show DAG list ──────────────────────────────────────────
echo "📋 Available DAGs:"
airflow dags list 2>/dev/null | grep f1
echo ""

# ── Trigger ingestion DAG ──────────────────────────────────
echo "🚀 Triggering dag_ingest_f1..."
airflow dags unpause dag_ingest_f1
airflow dags unpause dag_load_warehouse
airflow dags unpause dag_ingest_to_bronze
airflow dags trigger dag_ingest_f1
echo "✅ dag_ingest_f1 triggered"
echo ""

echo "=================================================="
echo "  ✅ DAGs triggered!"
echo ""
echo "  🌐 Monitor progress in Airflow UI:"
echo "     → Open port 8080 in Codespaces Ports tab"
echo "     → Login: admin / admin123"
echo ""
echo "  📋 Pipeline order:"
echo "     1. dag_ingest_f1       (~45-60 min)"
echo "     2. dag_load_warehouse  (~10 sec)"
echo ""
echo "  💡 Tip: After dag_ingest_f1 finishes,"
echo "     trigger dag_load_warehouse manually in the UI"
echo "=================================================="
echo ""