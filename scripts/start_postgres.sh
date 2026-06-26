#!/bin/bash
# =============================================================
# start_postgres.sh — Start PostgreSQL only
# Usage: bash scripts/start_postgres.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Starting PostgreSQL"
echo "=================================================="
echo ""

export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow
export PATH=$PATH:$HOME/.local/bin

echo "🐳 Starting PostgreSQL container..."
docker-compose -f docker/docker-compose.yml up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 4

docker exec f1_postgres pg_isready -U f1user -d f1_warehouse > /dev/null 2>&1 \
    && echo "✅ PostgreSQL is ready (port 5432)" \
    || echo "⚠️  PostgreSQL not ready yet — wait a few seconds"

echo ""
echo "=================================================="
echo "  🐳 PostgreSQL → localhost:5432"
echo "  🔑 user: f1user / pass: f1password"
echo "  📁 db:   f1_warehouse"
echo "=================================================="
echo ""