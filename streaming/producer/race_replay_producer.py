"""
Race Replay Producer — Step 08
----------------------------------
Reads historical lap time data from the Silver layer and publishes it
to Kafka topics in chronological order, simulating a live race broadcast.

Usage:
    python -m streaming.producer.race_replay_producer --season 2024 --round 1
    python -m streaming.producer.race_replay_producer --season 2024 --round 1 --speed 10
"""

import sys
import json
import time
import argparse

sys.path.insert(0, '/workspaces/f1-data-engineering')

from kafka import KafkaProducer
from streaming.producer.topic_config import KAFKA_BOOTSTRAP_SERVERS, TOPICS
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)


def get_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def replay_race(season: int, round_num: int, speed: float = 50.0):
    """
    Replays a race's lap-by-lap data through Kafka.

    speed: replay speed multiplier.
        1.0  = real F1 pace (~90s between laps per driver) — very slow for a demo
        50.0 = 50x faster (default — good for demos)
        0    = as fast as possible (no delay)
    """
    spark = get_spark("race_replay_producer")
    log.info(f"Loading lap data for season={season}, round={round_num}")

    laps_df = spark.sql(f"""
        SELECT season, round, driver_id, lap_number, position, lap_time, lap_time_ms
        FROM f1_catalog.silver.lap_times
        WHERE season = {season} AND round = {round_num}
        ORDER BY lap_number, position
    """)

    laps = [row.asDict() for row in laps_df.collect()]
    spark.stop()

    if not laps:
        log.info(f"No lap data found for season={season}, round={round_num}")
        return

    log.info(f"Loaded {len(laps)} lap events. Starting replay at speed={speed}x")

    producer = get_producer()
    topic = TOPICS["lap_events"]

    current_lap = None
    events_sent = 0

    for lap in laps:
        event = {
            "season":      lap["season"],
            "round":       lap["round"],
            "driver_id":   lap["driver_id"],
            "lap_number":  lap["lap_number"],
            "position":    lap["position"],
            "lap_time":    lap["lap_time"],
            "lap_time_ms": lap["lap_time_ms"],
            "event_timestamp": time.time(),
        }

        producer.send(topic, key=lap["driver_id"], value=event)
        events_sent += 1

        if current_lap is not None and lap["lap_number"] != current_lap and speed > 0:
            time.sleep(90 / speed)
        current_lap = lap["lap_number"]

        if events_sent % 20 == 0:
            log.info(f"Sent {events_sent}/{len(laps)} events...")

    producer.flush()
    producer.close()

    log.info(f"Replay complete - {events_sent} events sent to '{topic}'")
    print(f"\nRace replay complete: {events_sent} lap events sent to Kafka topic '{topic}'\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F1 Race Replay Producer")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--speed", type=float, default=50.0,
                         help="Replay speed multiplier (0 = as fast as possible, default: 50x)")
    args = parser.parse_args()

    replay_race(args.season, args.round, args.speed)