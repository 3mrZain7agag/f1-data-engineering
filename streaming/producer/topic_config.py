"""
Kafka Topic Configuration — Step 08
--------------------------------------
Central definition of all Kafka topics used in the F1 streaming layer.
"""

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

TOPICS = {
    "lap_events":          "f1.lap_events",
    "pit_stop_events":     "f1.pit_stop_events",
    "qualifying_events":   "f1.qualifying_events",
    "race_control_events": "f1.race_control_events",
}