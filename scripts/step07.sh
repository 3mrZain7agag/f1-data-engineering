#!/bin/bash
# =============================================================
# step07.sh — Run Great Expectations data quality checkpoints
# Validates Silver layer before allowing Gold layer to build
# Usage: bash scripts/step07.sh
# =============================================================

echo ""
echo "=================================================="
echo "  Step 07 — Data Quality (Great Expectations)"
echo "  Validates Silver layer before Gold build"
echo "=================================================="
echo ""

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

python -m quality.checkpoints.run_all_checks
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "=================================================="
    echo "  ✅ Step 07 Complete — Data Quality Passed!"
    echo ""
    echo "  Next step → bash scripts/step06.sh (rebuild Gold)"
    echo "=================================================="
else
    echo "=================================================="
    echo "  ❌ Step 07 FAILED — Data Quality issues found"
    echo "  Review the report above before proceeding to Gold"
    echo "=================================================="
fi
echo ""

exit $EXIT_CODE
