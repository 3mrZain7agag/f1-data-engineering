#!/bin/bash
# =============================================================
# view_gold.sh — Quick view of dbt Gold layer analytics tables
# Usage: bash scripts/view_gold.sh [season]
#   bash scripts/view_gold.sh          # defaults to 2024
#   bash scripts/view_gold.sh 2023     # specific season
# =============================================================

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

SEASON=${1:-2024}

python3 -c "
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName('view_gold') \
    .master('local[*]') \
    .config('spark.driver.memory', '2g') \
    .getOrCreate()

spark.sparkContext.setLogLevel('ERROR')

WAREHOUSE = '/workspaces/f1-data-engineering/dbt/f1_gold/spark-warehouse/gold_gold.db'

print('── Driver Season Stats ($SEASON) ────────────────')
spark.read.parquet(f'{WAREHOUSE}/agg_driver_season_stats') \
    .filter('season = $SEASON') \
    .orderBy('total_points', ascending=False) \
    .show(10, truncate=False)

print('── Constructor Season Stats ($SEASON) ───────────')
spark.read.parquet(f'{WAREHOUSE}/agg_constructor_season_stats') \
    .filter('season = $SEASON') \
    .orderBy('total_points', ascending=False) \
    .show(10, truncate=False)

print('── Circuit Stats (all-time) ─────────────────────')
spark.read.parquet(f'{WAREHOUSE}/agg_circuit_stats') \
    .orderBy('total_races', ascending=False) \
    .show(10, truncate=False)

spark.stop()
"