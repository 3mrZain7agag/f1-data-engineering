#!/bin/bash
# =============================================================
# step01.sh — Pull F1 historical data from Jolpica API
# Saves raw data to data/raw/ as CSV files + SQLite DB
# Usage:
#   bash scripts/step01.sh              # all seasons 2015-2026
#   bash scripts/step01.sh 2024         # single season
#   bash scripts/step01.sh 2022 2023    # multiple seasons
# =============================================================

echo ""
echo "=================================================="
echo "  Step 01 — F1 Data Ingestion"
echo "  Source: Jolpica API (free Ergast replacement)"
echo "=================================================="
echo ""

# ── Check data/raw directory ───────────────────────────────
mkdir -p data/raw

# ── Run ingestion ──────────────────────────────────────────
if [ $# -eq 0 ]; then
    echo "📡 Fetching all seasons one by one (2015–2026)..."
    echo "   ⚠️  Running one season at a time with 2min breaks"
    echo "   ⚠️  Total time: ~3-4 hours"
    echo ""
    for season in 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026; do
        echo "──────────────────────────────────────────"
        echo "📡 Fetching season $season..."
        python -m ingestion.extract_all --seasons $season
        if [ $season -ne 2026 ]; then
            echo "⏳ Waiting 2 minutes before next season..."
            sleep 120
        fi
    done
elif [ $# -eq 1 ]; then
    echo "📡 Fetching season: $1"
    echo ""
    python -m ingestion.extract_all --seasons "$1"
else
    echo "📡 Fetching seasons: $@"
    echo "   ⚠️  Running one season at a time with 2min breaks"
    echo ""
    for season in "$@"; do
        echo "──────────────────────────────────────────"
        echo "📡 Fetching season $season..."
        python -m ingestion.extract_all --seasons $season
        echo "⏳ Waiting 2 minutes before next season..."
        sleep 120
    done
fi

echo ""
echo "=================================================="
echo "  ✅ Step 01 Complete!"
echo ""
echo "  Output files in data/raw/:"
ls -lh data/raw/ 2>/dev/null | awk '{print "  " $0}'
echo ""
echo "  Next step → bash scripts/step02.sh"
echo "=================================================="
echo ""