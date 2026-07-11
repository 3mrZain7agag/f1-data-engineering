#!/bin/bash
# =============================================================
# step09.sh — Export Gold layer tables to CSV for Power BI
# Usage: bash scripts/step09.sh
# =============================================================

set -e

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo ""
echo "📊 Exporting Gold layer tables to CSV..."
echo ""

python3 -m export.export_gold_to_csv

echo ""
echo "✅ Export complete — check exports/gold/"
echo "   Download these files and load them into Power BI Desktop"
echo "   (Get Data → Text/CSV)"
echo ""