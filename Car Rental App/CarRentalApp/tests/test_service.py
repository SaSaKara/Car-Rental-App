import tempfile
from pathlib import Path
import datetime

from src.storage import JsonStorage
from src.service import CarRentalService

def test_add_rent_return_flow():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        storage = JsonStorage(str(data_dir))
        svc = CarRentalService(storage)

        svc.add_vehicle("Renault Clio", "34abc456", 500)
        vehicles = svc.list_vehicles()
        assert len(vehicles) == 1
        assert vehicles[0].plate == "34 ABC 456"
        assert vehicles[0].status == "AVAILABLE"

        start = datetime.date(2026, 2, 20)
        end = datetime.date(2026, 2, 22)
        days, fee, model = svc.rent_vehicle("34 ABC 456", start, end)
        assert days == 3
        assert fee == 1500
        assert model == "Renault Clio"

        v = svc.list_vehicles()[0]
        assert v.status == "RENTED"

        svc.return_vehicle("34ABC456")
        v = svc.list_vehicles()[0]
        assert v.status == "AVAILABLE"