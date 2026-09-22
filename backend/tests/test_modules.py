import pytest
from app.services.value_normalizer import expand_abbreviations, get_canonical_field_name, is_missing_value
from app.gis.crs_utils import estimate_utm_crs
import geopandas as gpd
from shapely.geometry import Polygon

def test_value_normalizer():
    assert expand_abbreviations("RES") == "Residential"
    assert expand_abbreviations("COMM") == "Commercial"
    assert get_canonical_field_name("area_sq_m") == "area_sqm"
    assert is_missing_value("N/A") is True
    assert is_missing_value("valid") is False

def test_crs_utils():
    gdf = gpd.GeoDataFrame(
        [{"name": "test"}],
        geometry=[Polygon([(77.59, 12.97), (77.591, 12.97), (77.591, 12.971), (77.59, 12.971)])],
        crs="EPSG:4326"
    )
    utm = estimate_utm_crs(gdf)
    assert utm.startswith("EPSG:32")

def test_security_secret_key_configuration():
    from app.config import settings
    from app.services.auth_service import SECRET_KEY as S1
    from app.services.auth_dependency import SECRET_KEY as S2
    assert S1 == settings.SECRET_KEY
    assert S2 == settings.SECRET_KEY


def test_feature_matching_identity_score():
    from app.ai.attribute_matcher import calculate_identity_score

    # Exact match
    score, field, s, t = calculate_identity_score({"parcel_id": "P005"}, {"parcel_id": "P005"})
    assert score == 1.0
    assert field == "parcel_id"

    # Exact match with casing/punctuation differences
    score, field, s, t = calculate_identity_score({"parcel_id": "p-005"}, {"parcel_id": "P005"})
    assert score == 1.0

    # Partial / Substring match
    score, field, s, t = calculate_identity_score({"khasra_no": "1025"}, {"khasra_no": "1025/1"})
    assert score == 0.85

    # Conflicting identity
    score, field, s, t = calculate_identity_score({"parcel_id": "P001"}, {"parcel_id": "P002"})
    assert score == 0.0

    # Missing identity
    score, field, s, t = calculate_identity_score({"land_use": "Residential"}, {"land_use": "Residential"})
    assert score == 0.5


def test_feature_matching_match_170_confidence():
    from app.ai.attribute_matcher import compare_attributes
    from app.ai.matching_engine import calculate_ml_confidence, load_match_model

    src_attrs = {
        "parcel_id": "P005",
        "land_use": "Residential",
        "area": 150,
        "survey_year": 2026,
        "source": "Drone Survey"
    }
    tgt_attrs = {
        "parcel_id": "P005",
        "land_use": "Agricultural",
        "area": 1500,
        "survey_year": 2020,
        "source": "Cadastral Baseline"
    }

    comp = compare_attributes(src_attrs, tgt_attrs)
    assert comp["identity_score"] == 1.0
    # survey_year and source ignored, area similarity = 0.10, land_use similarity = 0.25
    assert comp["matched_fields"] == 3
    assert comp["attribute_score"] > 0.50

    model = load_match_model()
    confidence = calculate_ml_confidence(
        model=model,
        spatial_score=0.4087,
        attribute_score=comp["attribute_score"],
        geometry_similarity=0.18,
        proximity_score=0.9424,
        distance=2.879,
        identity_score=comp["identity_score"]
    )
    # Must be high confidence (> 0.75) for identical parcel_id in close proximity
    assert confidence >= 0.75
    assert confidence <= 1.0


def test_feature_matching_conflicting_parcel_id():
    from app.ai.attribute_matcher import compare_attributes
    from app.ai.matching_engine import calculate_ml_confidence, load_match_model

    src_attrs = {"parcel_id": "P001", "land_use": "Residential"}
    tgt_attrs = {"parcel_id": "P002", "land_use": "Residential"}

    comp = compare_attributes(src_attrs, tgt_attrs)
    assert comp["identity_score"] == 0.0

    model = load_match_model()
    confidence = calculate_ml_confidence(
        model=model,
        spatial_score=0.45,
        attribute_score=comp["attribute_score"],
        geometry_similarity=0.30,
        proximity_score=0.90,
        distance=3.0,
        identity_score=comp["identity_score"]
    )
    # Must be low confidence when parcel IDs conflict
    assert confidence < 0.40
