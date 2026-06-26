#!/bin/bash
# =============================================================
# stop_airflow.sh — Stop Airflow webserver + scheduler only
# Usage: bash scripts/stop_airflow.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Stopping Apache Airflow"
echo "=================================================="
echo ""

pkill -f "airflow webserver" 2>/dev/null \
    && echo "✅ Airflow Webserver stopped" \
    || echo "   (Webserver was not running)"

pkill -f "airflow scheduler" 2>/dev/null \
    && echo "✅ Airflow Scheduler stopped" \
    || echo "   (Scheduler was not running)"

echo ""
echo "=================================================="
echo "  ✅ Airflow stopped"
echo "  → Run: bash scripts/start_airflow.sh to restart"
echo "=================================================="
echo ""