"""
CRS utilities for metric-distance spatial analysis.

IMPORTANT: Never use EPSG:4326 (geographic) coordinates for metric
distance calculations. Always project to an appropriate CRS first.
"""

from typing import Optional
import geopandas as gpd
from pyproj import CRS


def estimate_utm_crs(gdf: gpd.GeoDataFrame) -> str:
    """
    Estimate the most appropriate UTM CRS for a GeoDataFrame
    based on the centroid of its bounding box.

    Returns an EPSG code string like 'EPSG:32643'.
    """
    if gdf.empty:
        raise ValueError("Cannot estimate UTM CRS: GeoDataFrame is empty")

    # Ensure we work in geographic coords to get the centroid lon/lat
    if gdf.crs is None:
        raise ValueError("Cannot estimate UTM CRS: GeoDataFrame has no CRS set")

    geo_gdf = gdf
    if not CRS.from_user_input(gdf.crs).is_geographic:
        geo_gdf = gdf.to_crs("EPSG:4326")

    bounds = geo_gdf.total_bounds          # [min_x, min_y, max_x, max_y]
    centroid_lon = (bounds[0] + bounds[2]) / 2.0
    centroid_lat = (bounds[1] + bounds[3]) / 2.0

    # UTM zone number from longitude
    utm_zone = int((centroid_lon + 180) / 6) + 1

    # Northern or southern hemisphere
    if centroid_lat >= 0:
        epsg = 32600 + utm_zone      # WGS84 / UTM zone N
    else:
        epsg = 32700 + utm_zone      # WGS84 / UTM zone S

    return f"EPSG:{epsg}"


def to_projected(gdf: gpd.GeoDataFrame, target_crs: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Convert a GeoDataFrame to a suitable projected CRS for metric operations.

    If target_crs is provided, uses that. Otherwise auto-detects the UTM zone.
    Returns a new GeoDataFrame; never modifies the original.
    """
    if gdf.empty:
        return gdf.copy()

    crs_to_use = target_crs or estimate_utm_crs(gdf)
    return gdf.to_crs(crs_to_use)


def to_geographic(gdf: gpd.GeoDataFrame, geographic_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """
    Convert a projected GeoDataFrame back to geographic CRS.
    Typically used after metric computations before storage.
    """
    if gdf.empty:
        return gdf.copy()
    return gdf.to_crs(geographic_crs)
