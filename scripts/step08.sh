#!/bin/bash
# =============================================================
# step08.sh — Kafka Streaming: Race Replay + Spark Consumer
# Usage:
#   bash scripts/step08.sh                    # replay 2024 round 1
#   bash scripts/step08.sh 2023 5             # replay season 2023 round 5
# =============================================================

SEASON=${1:-2024}
ROUND=${2:-1}

echo ""
echo "=================================================="
echo "  Step 08 — Kafka Streaming Layer"
echo "  Race Replay: Season $SEASON, Round $ROUND"
echo "=================================================="
echo ""

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# ── Check Kafka is running ─────────────────────────────────
echo "🔍 Checking Kafka connection..."
docker exec f1_kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Kafka is not running!"
    echo "   Run: bash scripts/start_kafka.sh first"
    exit 1
fi
echo "✅ Kafka is ready"
echo ""

echo "📋 Ensuring Kafka topic exists..."
docker exec f1_kafka kafka-topics --bootstrap-server localhost:9092 --create --topic f1.lap_events --partitions 3 --replication-factor 1 --if-not-exists
echo ""

# ── Start the Streaming Consumer in the background ─────────
echo "⚡ Starting Spark Streaming Consumer (background)..."
nohup python -m streaming.consumer.spark_streaming_consumer > /tmp/f1_consumer.log 2>&1 &
CONSUMER_PID=$!
echo "   Consumer PID: $CONSUMER_PID"
echo "$CONSUMER_PID" > /tmp/f1_consumer.pid
echo "⏳ Waiting for consumer to initialize..."
sleep 20
echo ""

# ── Run the Producer (race replay) ─────────────────────────
echo "📡 Starting race replay producer..."
python -m streaming.producer.race_replay_producer --season "$SEASON" --round "$ROUND" --speed 50
echo ""

# ── Wait for the consumer to process the final batch ───────
echo "⏳ Waiting for consumer to process remaining events..."
sleep 15

echo ""
echo "=================================================="
echo "  ✅ Step 08 Complete!"
echo ""
echo "  🌐 Kafka UI     → Open port 8085 in Ports tab"
echo "  📁 Bronze data  → s3://f1-bronze/kafka/lap_events/"
echo ""
echo "  Consumer still running in background (PID: $CONSUMER_PID)"
echo "  → To stop it: kill \$(cat /tmp/f1_consumer.pid)"
echo "  → Logs: tail -f /tmp/f1_consumer.log"
echo "=================================================="
echo ""