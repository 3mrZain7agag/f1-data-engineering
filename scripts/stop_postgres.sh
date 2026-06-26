#!/bin/bash
# =============================================================
# stop_postgres.sh — Stop PostgreSQL only
# Usage: bash scripts/stop_postgres.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Stopping PostgreSQL"
echo "=================================================="
echo ""

docker-compose -f docker/docker-compose.yml stop postgres
docker-compose -f docker/docker-compose.yml rm -f postgres

echo "✅ PostgreSQL stopped"
echo ""