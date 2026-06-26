#!/bin/bash
# =============================================================
# setup.sh — Run this ONCE after cloning the repo
# Sets up the full project environment from scratch
# Usage: bash scripts/setup.sh
# =============================================================

set -e  # Stop if any command fails

echo ""
echo "=================================================="
echo "  F1 Data Engineering — Project Setup"
echo "=================================================="
echo ""

# ── Step 1: Install Python dependencies ───────────────────
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt -q
echo "✅ Python dependencies installed"
echo ""

# ── Step 1.5: Install Java 17 (required for Spark) ──────────
echo "☕ Installing Java 17..."
sudo apt-get update -q && sudo apt-get install -y openjdk-17-jdk -q
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
echo "✅ Java 17 installed"
echo ""

# ── Step 2: Install Apache Airflow ────────────────────────
echo "✈️  Installing Apache Airflow..."
pip install apache-airflow==2.9.3 -q \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt"
echo "✅ Airflow installed"
echo ""

# ── Step 3: Initialize Airflow ─────────────────────────────
echo "⚙️  Initializing Airflow..."
export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow
export PATH=$PATH:$HOME/.local/bin

airflow db migrate

# Create admin user
airflow users create \
    --username admin \
    --firstname Amr \
    --lastname Hagag \
    --role Admin \
    --email amr.hagag.prof@gmail.com \
    --password admin123 2>/dev/null || echo "   (admin user already exists)"

# Configure Airflow settings
sed -i "s|load_examples = True|load_examples = False|" airflow/airflow.cfg 2>/dev/null || true
sed -i "s|dags_folder = .*|dags_folder = /workspaces/f1-data-engineering/orchestration/dags|" airflow/airflow.cfg 2>/dev/null || true
sed -i "s|enable_proxy_fix = False|enable_proxy_fix = True|" airflow/airflow.cfg 2>/dev/null || true

echo "✅ Airflow initialized"
echo ""

# ── Step 4: Start PostgreSQL ───────────────────────────────
echo "🐳 Starting PostgreSQL..."
docker-compose -f docker/docker-compose.yml up -d
echo "✅ PostgreSQL started"
echo ""

# ── Step 5: Wait for PostgreSQL ────────────────────────────
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# ── Step 6: Create database schema ────────────────────────
echo "🏗️  Creating Star Schema tables..."
docker exec -i f1_postgres psql -U f1user -d f1_warehouse < warehouse/schema.sql
echo "✅ Schema created"
echo ""

echo "=================================================="
echo "  ✅ Setup Complete!"
echo ""
echo "  Next steps:"
echo "  → Run: bash scripts/start.sh    (start all services)"
echo "  → Then: bash scripts/step01.sh  (pull F1 data)"
echo "=================================================="
echo ""

# ── Fix: Enable Airflow REST API for VS Code extension ─────
echo "🔌 Enabling Airflow REST API..."
python3 -c "
content = open('airflow/airflow.cfg').read()
content = content.replace(
    'auth_backends = airflow.api.auth.backend.session',
    'auth_backends = airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
)
open('airflow/airflow.cfg', 'w').write(content)
print('Done')
"
echo "✅ REST API enabled"
