#!/bin/bash
# =============================================================
# step01.sh — Pull F1 historical data from Jolpica API
# Saves raw data to data/raw/ as CSV files + SQLite DB
# Usage:
#   bash scripts/step01.sh              # all seasons 2015-2024
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
    echo "📡 Fetching all seasons (2015–2024)..."
    echo "   ⚠️  This will take ~45-60 minutes due to API rate limiting"
    echo ""
    python -m ingestion.extract_all
else
    echo "📡 Fetching season(s): $@"
    echo ""
    python -m ingestion.extract_all --seasons "$@"
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