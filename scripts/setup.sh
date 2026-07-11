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

# ── Step 1.5: Install Java 17 (required for Spark) ────────
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

# ── Step 2.5: Install dbt-core + dbt-spark ────────────────
echo "🏗️  Installing dbt..."
pip install dbt-core dbt-spark -q || true
echo "✅ dbt installed"
echo ""

# ── Step 2.6: Install Great Expectations ──────────────────
echo "🔍 Installing Great Expectations..."
pip install great_expectations==0.18.19 -q || true
echo "✅ Great Expectations installed"
echo ""

# ── Step 2.7: Install Kafka Python client ─────────────────
echo "📨 Installing kafka-python-ng..."
pip install kafka-python-ng==2.2.2 -q || true
echo "✅ kafka-python-ng installed"
echo ""

# ── Step 2.8: Pin typing_extensions (fixes Airflow/pydantic conflict) ──
echo "🔧 Fixing typing_extensions version conflict..."
pip install "typing_extensions==4.16.0" --no-deps --force-reinstall -q --break-system-packages
echo "✅ typing_extensions pinned"
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

# ── Step 3.5: Configure dbt profile ───────────────────────
echo "🔧 Configuring dbt profile..."
mkdir -p ~/.dbt
cat > ~/.dbt/profiles.yml << "PROFILEEOF"
f1_gold:
  target: dev
  outputs:
    dev:
      type: spark
      method: session
      schema: gold
      host: localhost
      port: 7077
      cluster: local
      connect_retries: 3
      connect_timeout: 60
      server_side_parameters:
        spark.sql.extensions: "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
        spark.sql.catalog.f1_catalog: "org.apache.iceberg.spark.SparkCatalog"
        spark.sql.catalog.f1_catalog.type: "hadoop"
        spark.sql.catalog.f1_catalog.warehouse: "s3a://f1-silver/"
        spark.sql.catalog.spark_catalog: "org.apache.iceberg.spark.SparkSessionCatalog"
        spark.sql.catalog.spark_catalog.type: "hive"
        spark.hadoop.fs.s3a.endpoint: "http://localhost:9000"
        spark.hadoop.fs.s3a.access.key: "f1minio"
        spark.hadoop.fs.s3a.secret.key: "f1minio123"
        spark.hadoop.fs.s3a.path.style.access: "true"
        spark.hadoop.fs.s3a.impl: "org.apache.hadoop.fs.s3a.S3AFileSystem"
        spark.hadoop.fs.s3a.aws.credentials.provider: "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
        spark.hadoop.fs.s3a.connection.ssl.enabled: "false"
        spark.jars.packages: "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262"
PROFILEEOF
echo "✅ dbt profile configured"
echo ""

# ── Step 4: Start Docker services ─────────────────────────
echo "🐳 Starting PostgreSQL + MinIO + Spark..."
docker-compose -f docker/docker-compose.yml up -d
echo "✅ Docker services started"
echo ""

# ── Step 5: Wait for services to be ready ─────────────────
echo "⏳ Waiting for services to be ready..."
for i in {1..30}; do
    if docker exec f1_postgres psql -U f1user -d f1_warehouse -c "SELECT 1" > /dev/null 2>&1; then
        echo "  Postgres and f1_warehouse database are ready"
        break
    fi
    echo "  Waiting for f1_warehouse database... ($i/30)"
    sleep 2
done

# ── Step 6: Create database schema ────────────────────────
echo "🏗️  Creating Star Schema tables..."
docker exec -i f1_postgres psql -U f1user -d f1_warehouse < warehouse/schema.sql
echo "✅ Schema created"
echo ""

# ── Step 7: Create MinIO buckets ──────────────────────────
echo "🪣 Creating MinIO buckets..."
python3 -c "
import boto3
from botocore.client import Config
c = boto3.client('s3', endpoint_url='http://localhost:9000',
    aws_access_key_id='f1minio', aws_secret_access_key='f1minio123',
    config=Config(signature_version='s3v4'), region_name='us-east-1')
for bucket in ['f1-bronze', 'f1-silver', 'f1-gold']:
    try:
        c.head_bucket(Bucket=bucket)
        print(f'  {bucket} already exists')
    except:
        c.create_bucket(Bucket=bucket)
        print(f'  {bucket} created')
"
echo "✅ MinIO buckets ready"
echo ""

# ── Step 8: Enable Airflow REST API ───────────────────────
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
echo ""

echo "=================================================="
echo "  ✅ Setup Complete!"
echo ""
echo "  Next steps:"
echo "  → Run: bash scripts/start.sh    (start all services)"
echo "  → Then: bash scripts/step01.sh  (pull F1 data)"
echo "=================================================="
echo ""