#!/bin/bash
# =============================================================
# stop.sh — Gracefully stop all running services
# Usage: bash scripts/stop.sh
# =============================================================

echo ""
echo "=================================================="
echo "  F1 Data Engineering — Stopping All Services"
echo "=================================================="
echo ""

# ── Stop Airflow processes ─────────────────────────────────
echo "✈️  Stopping Airflow..."
pkill -f "airflow webserver" 2>/dev/null && echo "✅ Airflow Webserver stopped" || echo "   (Webserver was not running)"
pkill -f "airflow scheduler" 2>/dev/null && echo "✅ Airflow Scheduler stopped" || echo "   (Scheduler was not running)"
echo ""

# ── Stop PostgreSQL ────────────────────────────────────────
echo "🐳 Stopping PostgreSQL..."
docker-compose -f docker/docker-compose.yml down
echo "✅ PostgreSQL stopped"
echo ""

echo "=================================================="
echo "  ✅ All services stopped cleanly"
echo "  → Run: bash scripts/start.sh to restart"
echo "=================================================="
echo ""