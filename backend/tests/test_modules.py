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
