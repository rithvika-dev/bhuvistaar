import pytest
from app.services.conflict_service import (
    calculate_numeric_discrepancy,
    normalize_value_str,
    try_parse_float,
    IGNORED_METADATA_FIELDS,
    IDENTITY_FIELDS,
    NUMERIC_MEASUREMENT_FIELDS,
)


def test_conflict_ignored_fields():
    assert "source" in IGNORED_METADATA_FIELDS
    assert "survey_year" in IGNORED_METADATA_FIELDS
    assert "capture_date" in IGNORED_METADATA_FIELDS
    assert "crs" in IGNORED_METADATA_FIELDS


def test_conflict_identity_fields():
    assert "parcel_id" in IDENTITY_FIELDS
    assert "khasra_no" in IDENTITY_FIELDS
    assert "ulpin" in IDENTITY_FIELDS


def test_numeric_discrepancy_tolerance():
    # 2% difference -> within 5% tolerance -> None (no conflict)
    assert calculate_numeric_discrepancy(1000, 1020, tolerance=0.05) is None
    assert calculate_numeric_discrepancy("1500", "1550", tolerance=0.05) is None

    # 15% difference -> low severity
    res_low = calculate_numeric_discrepancy(100, 115, tolerance=0.05)
    assert res_low is not None
    rel_diff, sev, conf, desc, sugg = res_low
    assert sev == "low"
    assert 0.70 <= conf <= 0.85

    # 35% difference -> medium severity
    res_med = calculate_numeric_discrepancy(100, 135, tolerance=0.05)
    assert res_med is not None
    rel_diff, sev, conf, desc, sugg = res_med
    assert sev == "medium"
    assert 0.80 <= conf <= 0.95

    # 80% difference -> high severity
    res_high = calculate_numeric_discrepancy(150, 1500, tolerance=0.05)
    assert res_high is not None
    rel_diff, sev, conf, desc, sugg = res_high
    assert sev == "high"
    assert conf >= 0.90
    assert "Area / measurement differs by" in desc


def test_normalize_value_str():
    assert normalize_value_str("  Residential  ") == "residential"
    assert normalize_value_str(None) == ""
    assert normalize_value_str(123) == "123"


def test_try_parse_float():
    assert try_parse_float("1500.50 sqm") == 1500.50
    assert try_parse_float(120) == 120.0
    assert try_parse_float("N/A") is None
    assert try_parse_float(None) is None
