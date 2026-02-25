from __future__ import annotations
from typing import List, Optional, Tuple

from .models import Vehicle
from .storage import JsonStorage
from .utils import normalize_plate, format_log


class CarRentalService:
    """Business logic layer independent from UI."""

    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def _get_all(self) -> List[Vehicle]:
        return self.storage.load_vehicles()

    def _save_all(self, vehicles: List[Vehicle]) -> None:
        self.storage.save_vehicles(vehicles)

    def _find_by_plate(self, vehicles: List[Vehicle], plate: str) -> Optional[Vehicle]:
        for v in vehicles:
            if v.plate == plate:
                return v
        return None

    # ---------- Public API ----------

    def list_vehicles(self) -> List[Vehicle]:
        return self._get_all()

    def add_vehicle(self, model_name: str, plate_raw: str, daily_price: int) -> None:
        model_name = (model_name or "").strip().title()
        if not model_name:
            raise ValueError("Model name is required.")
        plate = normalize_plate(plate_raw)

        if not isinstance(daily_price, int) or daily_price <= 0:
            raise ValueError("Daily price must be a positive integer.")

        vehicles = self._get_all()
        if self._find_by_plate(vehicles, plate) is not None:
            raise ValueError("This license plate is already registered.")

        v = Vehicle(model_name=model_name, plate=plate, daily_price=daily_price, status="AVAILABLE")
        vehicles.append(v)
        self._save_all(vehicles)

        self.storage.append_record(format_log(
            "VEHICLE_ADDED", model=model_name, plate=plate, price=daily_price
        ))

    def rent_vehicle(self, plate_raw: str, start_date, end_date) -> Tuple[int, int, str]:
        """
        Rent a vehicle for a date range.
        Returns (days, fee, model_name)
        """
        plate = normalize_plate(plate_raw)
        days = (end_date - start_date).days + 1
        if days <= 0:
            raise ValueError("End date cannot be earlier than start date.")

        vehicles = self._get_all()
        v = self._find_by_plate(vehicles, plate)
        if v is None:
            raise ValueError("No vehicle found with that license plate.")
        if v.status != "AVAILABLE":
            raise ValueError("This vehicle is already rented.")

        v.status = "RENTED"
        fee = days * v.daily_price
        self._save_all(vehicles)

        stats = self.storage.load_stats()
        stats["total_revenue"] += fee
        self.storage.save_stats(stats)

        self.storage.append_record(format_log(
            "VEHICLE_RENTED", model=v.model_name, plate=plate, days=days, fee=fee
        ))
        return days, fee, v.model_name

    def return_vehicle(self, plate_raw: str) -> str:
        plate = normalize_plate(plate_raw)

        vehicles = self._get_all()
        v = self._find_by_plate(vehicles, plate)
        if v is None:
            raise ValueError("No vehicle found with that license plate.")
        if v.status != "RENTED":
            raise ValueError("This vehicle is not currently rented.")

        v.status = "AVAILABLE"
        self._save_all(vehicles)

        self.storage.append_record(format_log(
            "VEHICLE_RETURNED", model=v.model_name, plate=plate
        ))
        return v.model_name

    def edit_vehicle(self, old_plate_raw: str, new_model: str, new_plate_raw: str, new_daily_price: int) -> None:
        old_plate = normalize_plate(old_plate_raw)
        new_plate = normalize_plate(new_plate_raw)
        new_model = (new_model or "").strip().title()
        if not new_model:
            raise ValueError("New model name is required.")
        if not isinstance(new_daily_price, int) or new_daily_price <= 0:
            raise ValueError("New daily price must be a positive integer.")

        vehicles = self._get_all()
        target = self._find_by_plate(vehicles, old_plate)
        if target is None:
            raise ValueError("No vehicle found with that license plate.")

        # If plate changes, ensure uniqueness
        if new_plate != old_plate and self._find_by_plate(vehicles, new_plate) is not None:
            raise ValueError("Another vehicle already uses this license plate.")

        old_model = target.model_name
        target.model_name = new_model
        target.plate = new_plate
        target.daily_price = new_daily_price
        self._save_all(vehicles)

        self.storage.append_record(format_log(
            "VEHICLE_UPDATED",
            old_model=old_model, old_plate=old_plate,
            new_model=new_model, new_plate=new_plate,
            new_price=new_daily_price
        ))

    def delete_vehicle(self, plate_raw: str) -> str:
        plate = normalize_plate(plate_raw)

        vehicles = self._get_all()
        target = self._find_by_plate(vehicles, plate)
        if target is None:
            raise ValueError("No vehicle found with that license plate.")

        vehicles = [v for v in vehicles if v.plate != plate]
        self._save_all(vehicles)

        self.storage.append_record(format_log(
            "VEHICLE_DELETED", model=target.model_name, plate=plate
        ))
        return target.model_name

    def get_report(self):
        vehicles = self._get_all()
        stats = self.storage.load_stats()
        total_revenue = stats.get("total_revenue", 0)
        available = [v for v in vehicles if v.status == "AVAILABLE"]
        available_count = len(available)
        return total_revenue, available, available_count

    def get_recent_logs(self, limit: int = 20) -> List[str]:
        logs = self.storage.load_records()
        return list(reversed(logs[-limit:]))