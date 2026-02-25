import pytest
from src.utils import normalize_plate

def test_plate_normalization():
    assert normalize_plate("34abc456") == "34 ABC 456"
    assert normalize_plate("06 AB 1234") == "06 AB 1234"
    assert normalize_plate(" 34  ABC   456 ") == "34 ABC 456"

def test_plate_invalid():
    with pytest.raises(ValueError):
        normalize_plate("abcd")
    with pytest.raises(ValueError):
        normalize_plate("34 123 ABC")