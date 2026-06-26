#!/bin/bash
# =============================================================
# start_airflow.sh — Start Airflow webserver + scheduler only
# Usage: bash scripts/start_airflow.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Starting Apache Airflow"
echo "=================================================="
echo ""

export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow
export PATH=$PATH:$HOME/.local/bin

# ── Stop any existing Airflow processes ────────────────────
echo "🔄 Stopping any existing Airflow processes..."
pkill -f "airflow webserver" 2>/dev/null || true
pkill -f "airflow scheduler" 2>/dev/null || true
sleep 2

# ── Start Airflow Webserver ────────────────────────────────
echo "🌐 Starting Airflow Webserver on port 8080..."
nohup airflow webserver --port 8080 > airflow/logs/webserver.log 2>&1 &
echo "   PID: $!"
echo "✅ Airflow Webserver started"
echo ""

# ── Start Airflow Scheduler ────────────────────────────────
echo "⏰ Starting Airflow Scheduler..."
nohup airflow scheduler > airflow/logs/scheduler_main.log 2>&1 &
echo "   PID: $!"
echo "✅ Airflow Scheduler started"
echo ""

echo "⏳ Waiting for Airflow UI to be ready..."
sleep 8

echo ""
echo "=================================================="
echo "  ✈️  Airflow UI → Open port 8080 in Ports tab"
echo "  🔑 Login      → admin / admin123"
echo "=================================================="
echo ""