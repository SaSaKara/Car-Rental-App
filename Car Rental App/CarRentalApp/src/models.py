from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


VehicleStatus = Literal["AVAILABLE", "RENTED"]


@dataclass
class Vehicle:
    model_name: str
    plate: str           # Normalized plate format (e.g., "34 ABC 456")
    daily_price: int
    status: VehicleStatus = "AVAILABLE"

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "plate": self.plate,
            "daily_price": self.daily_price,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: dict) -> "Vehicle":
        return Vehicle(
            model_name=str(d.get("model_name", "")).strip(),
            plate=str(d.get("plate", "")).strip(),
            daily_price=int(d.get("daily_price", 0)),
            status=d.get("status", "AVAILABLE"),
        )