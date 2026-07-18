#!/bin/bash
# =============================================================
# refresh_pipeline.sh — Push newly-pulled data through the whole
# downstream pipeline in the correct order.
#
# WHY THIS EXISTS: pulling new data with step01.sh only updates
# data/raw/. It does NOT automatically flow through Bronze, Silver,
# the dbt Gold layer, or the Power BI/ML exports — each of those is
# a separate step that only processes whatever's already in the
# layer before it. It's easy to pull new season/round data, then
# wonder why it's missing from exports/gold/ or the ML predictions,
# simply because steps 04-09 were never re-run.
#
# This script runs the full downstream chain in the right order so
# that doesn't happen. Run it any time after step01.sh pulls new data.
#
# Usage: bash scripts/refresh_pipeline.sh
# =============================================================

set -e

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo ""
echo "=================================================="
echo "  Refreshing pipeline: Bronze → Silver → Quality → Gold → Export"
echo "=================================================="
echo ""

echo "── Step 04: Bronze ──────────────────────────────"
bash scripts/step04.sh

echo ""
echo "── Step 05: Silver ──────────────────────────────"
bash scripts/step05.sh

echo ""
echo "── Step 07: Data Quality ────────────────────────"
bash scripts/step07.sh

echo ""
echo "── Step 06: Gold (dbt) ──────────────────────────"
rm -rf dbt/f1_gold/spark-warehouse dbt/f1_gold/target
bash scripts/step06.sh

echo ""
echo "── Step 09: Export Gold → CSV ───────────────────"
bash scripts/step09.sh

echo ""
echo "=================================================="
echo "  ✅ Pipeline refresh complete!"
echo "  Gold layer and exports/gold/ now reflect the"
echo "  latest data pulled via step01.sh."
echo ""
echo "  If you also use the ML pipeline (Step 10), rebuild"
echo "  its dataset next:"
echo "  → bash scripts/step10.sh"
echo "=================================================="
echo ""