from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict

from .models import Vehicle


class JsonStorage:
    """
    JSON-based persistence layer.

    Files:
    - vehicles.json: list of vehicles
    - records.json: list of log strings
    - stats.json: {"total_revenue": int}
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.vehicles_path = self.data_dir / "vehicles.json"
        self.records_path = self.data_dir / "records.json"
        self.stats_path = self.data_dir / "stats.json"

        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if not self.vehicles_path.exists():
            self._write_json(self.vehicles_path, [])
        if not self.records_path.exists():
            self._write_json(self.records_path, [])
        if not self.stats_path.exists():
            self._write_json(self.stats_path, {"total_revenue": 0})

    def _read_json(self, path: Path, default):
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError:
            # If corrupted, fall back to default (and do not crash UI)
            return default

    def _write_json(self, path: Path, data) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # Vehicles
    def load_vehicles(self) -> List[Vehicle]:
        raw = self._read_json(self.vehicles_path, [])
        if isinstance(raw, dict):
            # Backward-compat: convert dict values to list if needed
            raw = list(raw.values())
        if not isinstance(raw, list):
            raw = []
        return [Vehicle.from_dict(x) for x in raw if isinstance(x, dict)]

    def save_vehicles(self, vehicles: List[Vehicle]) -> None:
        self._write_json(self.vehicles_path, [v.to_dict() for v in vehicles])

    # Records / logs
    def load_records(self) -> List[str]:
        raw = self._read_json(self.records_path, [])
        if isinstance(raw, dict):
            raw = list(raw.values())
        if not isinstance(raw, list):
            raw = []
        return [str(x) for x in raw]

    def append_record(self, line: str) -> None:
        records = self.load_records()
        records.append(line)
        self._write_json(self.records_path, records)

    # Stats
    def load_stats(self) -> Dict[str, int]:
        raw = self._read_json(self.stats_path, {"total_revenue": 0})
        if not isinstance(raw, dict):
            raw = {"total_revenue": 0}
        if "total_revenue" not in raw or not isinstance(raw["total_revenue"], int):
            raw["total_revenue"] = 0
        return raw

    def save_stats(self, stats: Dict[str, int]) -> None:
        if "total_revenue" not in stats or not isinstance(stats["total_revenue"], int):
            stats["total_revenue"] = 0
        self._write_json(self.stats_path, stats)