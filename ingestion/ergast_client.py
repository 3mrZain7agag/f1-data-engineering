"""
Ergast API Client
-----------------
Wraps the free Ergast F1 REST API (https://ergast.com/mrd/).
- Auto-retry on transient failures (tenacity)
- Pagination support (Ergast caps responses at 'limit' rows)
- Rate limiting: 4 requests/second max (Ergast fair-use policy)
"""

import time
from typing import Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from utils.logger import get_logger

log = get_logger(__name__)

BASE_URL = "https://api.jolpi.ca/ergast/f1"
DEFAULT_LIMIT = 1000          # max rows per page
REQUEST_DELAY = 1.0           # seconds between requests (~1 req/s)


class ErgastClient:
    """Thin HTTP client for the Ergast REST API."""

    def __init__(self, base_url: str = BASE_URL, delay: float = REQUEST_DELAY):
        self.base_url = base_url
        self.delay    = delay
        self.session  = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ── Core fetcher ───────────────────────────────────────────────────────
    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=3, min=5, max=120),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _get(self, url: str, params: dict) -> dict:
        time.sleep(self.delay)
        log.info(f"GET {url}  params={params}")
        resp = self.session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(60)  # wait 60 seconds on rate limit
        resp.raise_for_status()
        return resp.json()

    # ── Paginated fetcher ──────────────────────────────────────────────────
    def _get_all(self, endpoint: str, data_keys: list[str]) -> list[dict]:
        """
        Fetch all pages for an endpoint and return the list of items.
        data_keys is the path into MRData, e.g. ['RaceTable', 'Races'].
        """
        offset = 0
        results: list[dict] = []

        while True:
            params = {"limit": DEFAULT_LIMIT, "offset": offset}
            url    = f"{self.base_url}/{endpoint}.json"
            data   = self._get(url, params)

            mr_data = data.get("MRData", {})
            total   = int(mr_data.get("total", 0))

            # Navigate nested keys to the list
            items: Any = mr_data
            for key in data_keys:
                items = items.get(key, {})
            if isinstance(items, list):
                results.extend(items)
            else:
                break

            offset += DEFAULT_LIMIT
            if offset >= total:
                break

        log.info(f"Fetched {len(results)} records from /{endpoint}")
        return results

    # ── Public API methods ─────────────────────────────────────────────────

    def get_races(self, season: int) -> list[dict]:
        return self._get_all(f"{season}", ["RaceTable", "Races"])

    def get_results(self, season: int, round_num: int) -> list[dict]:
        data = self._get(
            f"{self.base_url}/{season}/{round_num}/results.json",
            {"limit": DEFAULT_LIMIT}
        )
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("Results", []) if races else []

    def get_lap_times(self, season: int, round_num: int) -> list[dict]:
        """Returns all laps for a race as a flat list of {driver, lap, time}."""
        laps: list[dict] = []
        offset = 0

        while True:
            url    = f"{self.base_url}/{season}/{round_num}/laps.json"
            params = {"limit": DEFAULT_LIMIT, "offset": offset}
            data   = self._get(url, params)
            mr     = data.get("MRData", {})
            total  = int(mr.get("total", 0))
            races  = mr.get("RaceTable", {}).get("Races", [])

            if not races:
                break

            for lap in races[0].get("Laps", []):
                lap_number = lap.get("number")
                for timing in lap.get("Timings", []):
                    laps.append({
                        "lap_number": lap_number,
                        "driver_id":  timing.get("driverId"),
                        "position":   timing.get("position"),
                        "time":       timing.get("time"),
                    })

            offset += DEFAULT_LIMIT
            if offset >= total:
                break

        return laps

    def get_pit_stops(self, season: int, round_num: int) -> list[dict]:
        data = self._get(
            f"{self.base_url}/{season}/{round_num}/pitstops.json",
            {"limit": DEFAULT_LIMIT}
        )
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("PitStops", []) if races else []

    def get_qualifying(self, season: int, round_num: int) -> list[dict]:
        data = self._get(
            f"{self.base_url}/{season}/{round_num}/qualifying.json",
            {"limit": DEFAULT_LIMIT}
        )
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("QualifyingResults", []) if races else []

    def get_drivers(self, season: int) -> list[dict]:
        return self._get_all(f"{season}/drivers", ["DriverTable", "Drivers"])

    def get_constructors(self, season: int) -> list[dict]:
        return self._get_all(f"{season}/constructors", ["ConstructorTable", "Constructors"])

    def get_circuits(self, season: int) -> list[dict]:
        return self._get_all(f"{season}/circuits", ["CircuitTable", "Circuits"])
