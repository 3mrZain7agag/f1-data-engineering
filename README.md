# F1 Data Engineering — Step 01: Simple Python ETL

## What this does
Pulls 10 seasons (2015–2024) of F1 historical data from the free
[Ergast API](https://ergast.com/mrd/) and saves it locally as:
- `data/raw/*.csv` — one CSV per entity
- `data/raw/f1.db` — SQLite database with all entities as tables

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# Full run — all seasons 2015–2024
python -m ingestion.extract_all

# Single season (faster, good for testing)
python -m ingestion.extract_all --seasons 2024

# Multiple specific seasons
python -m ingestion.extract_all --seasons 2022 2023 2024
```

## Output files

| File | Description |
|------|-------------|
| `data/raw/races.csv` | Race calendar — date, circuit, season, round |
| `data/raw/results.csv` | Race results — position, points, status per driver |
| `data/raw/lap_times.csv` | Individual lap times per driver per race |
| `data/raw/pit_stops.csv` | Pit stop events with lap and duration |
| `data/raw/qualifying.csv` | Q1/Q2/Q3 times and grid positions |
| `data/raw/drivers.csv` | Driver profiles |
| `data/raw/constructors.csv` | Constructor/team profiles |
| `data/raw/circuits.csv` | Circuit metadata with coordinates |
| `data/raw/f1.db` | SQLite DB — all tables above |

## Quick validation query (SQLite)

```sql
-- Top 5 drivers by total points 2015–2024
SELECT driver_id, SUM(CAST(points AS REAL)) AS total_points
FROM results
GROUP BY driver_id
ORDER BY total_points DESC
LIMIT 5;
```

## Project structure

```
f1-de-project/
├── ingestion/
│   ├── ergast_client.py   ← API client (retry, pagination)
│   └── extract_all.py     ← Main ETL runner
├── utils/
│   └── logger.py          ← Structured JSON logging
├── data/raw/              ← Output CSVs + SQLite DB
├── requirements.txt
└── README.md
```
