#!/bin/bash
# =============================================================
# start.sh — Run this EVERY TIME you reopen the Codespace
# Starts all services: PostgreSQL, MinIO, Airflow
# Usage: bash scripts/start.sh
# =============================================================

echo ""
echo "=================================================="
echo "  F1 Data Engineering — Starting All Services"
echo "=================================================="
echo ""

# ── Pull latest code from GitHub ──────────────────────────
echo "⬇️  Pulling latest changes from GitHub..."
git pull origin main
echo "✅ Code is up to date"
echo ""

# ── Set Airflow environment ────────────────────────────────
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow
export PATH=$PATH:$HOME/.local/bin

# ── Start PostgreSQL + MinIO ───────────────────────────────
echo "🐳 Starting PostgreSQL + MinIO + Spark..."
docker-compose -f docker/docker-compose.yml up -d
echo "✅ PostgreSQL + MinIO + Spark running"
echo ""

# ── Wait for PostgreSQL ────────────────────────────────────
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 4
docker exec f1_postgres pg_isready -U f1user -d f1_warehouse > /dev/null 2>&1 \
    && echo "✅ PostgreSQL is accepting connections" \
    || echo "⚠️  PostgreSQL not ready yet — wait a few seconds and retry"
echo ""

# ── Start Airflow Webserver ────────────────────────────────
echo "🌐 Starting Airflow Webserver on port 8080..."
nohup airflow webserver --port 8080 > airflow/logs/webserver.log 2>&1 &
echo "   PID: $!"
echo "✅ Airflow Webserver started (background)"
echo ""

# ── Start Airflow Scheduler ────────────────────────────────
echo "⏰ Starting Airflow Scheduler..."
nohup airflow scheduler > airflow/logs/scheduler_main.log 2>&1 &
echo "   PID: $!"
echo "✅ Airflow Scheduler started (background)"
echo ""

# ── Wait for Webserver ─────────────────────────────────────
echo "⏳ Waiting for Airflow UI to be ready..."
sleep 8

echo ""
echo "=================================================="
echo "  ✅ All Services Running!"
echo ""
echo "  🌐 Airflow UI  → Open port 8080 in Ports tab"
echo "  🔑 Login       → admin / admin123"
echo "  🐳 PostgreSQL  → localhost:5432"
echo "  🪣 MinIO UI    → Open port 9001 in Ports tab"
echo "  🔑 MinIO Login → f1minio / f1minio123"
echo ""
echo "  📋 Available scripts:"
echo "  → bash scripts/step01.sh   Pull F1 data from API"
echo "  → bash scripts/step02.sh   Load data into warehouse"
echo "  → bash scripts/step04.sh   Upload to Bronze layer"
echo "  → bash scripts/stop.sh     Stop all services"
echo "=================================================="
echo ""
