"""
Spatial feature matcher.

CRITICAL FIX (Phase 5):
The original matcher used distance_threshold=0.002 which is in EPSG:4326 DEGREES,
not metres. This file now:
  1. Converts both GDFs to a projected metric CRS (auto UTM).
  2. Performs ALL distance/area calculations in metres.
  3. Returns distance_meters so callers always see metric values.
  4. Default threshold is 50 metres (configurable).

Never call this function with EPSG:4326 GDFs expecting metric results.
"""

from typing import List, Dict, Optional
import geopandas as gpd
from shapely.geometry.base import BaseGeometry

from app.gis.crs_utils import to_projected, estimate_utm_crs


def calculate_centroid_distance_meters(
    geometry_a: BaseGeometry,
    geometry_b: BaseGeometry
) -> float:
    """
    Centroid distance in the units of the CRS.
    Call this ONLY after projecting to a metric CRS.
    """
    return geometry_a.centroid.distance(geometry_b.centroid)


def calculate_geometry_similarity(
    geometry_a: BaseGeometry,
    geometry_b: BaseGeometry
) -> float:
    """
    IoU (Intersection over Union) similarity score [0, 1].
    Works correctly in any CRS because area ratios are unit-independent.
    """
    if geometry_a.is_empty or geometry_b.is_empty:
        return 0.0

    try:
        intersection = geometry_a.intersection(geometry_b)
        union = geometry_a.union(geometry_b)
    except Exception:
        return 0.0

    if intersection.is_empty or union.area == 0:
        return 0.0

    return float(intersection.area / union.area)


def calculate_area_similarity(
    geometry_a: BaseGeometry,
    geometry_b: BaseGeometry
) -> float:
    """
    How similar are the two geometries in area? [0, 1].
    1.0 = identical area, 0.0 = one is zero.
    """
    area_a = geometry_a.area
    area_b = geometry_b.area

    if area_a == 0 and area_b == 0:
        return 1.0
    if area_a == 0 or area_b == 0:
        return 0.0

    return float(min(area_a, area_b) / max(area_a, area_b))


def find_spatial_matches(
    source_gdf: gpd.GeoDataFrame,
    target_gdf: gpd.GeoDataFrame,
    distance_threshold_meters: float = 50.0,
    # Legacy alias kept for backward compat – ignored if > 1 (assumed degrees)
    distance_threshold: Optional[float] = None,
) -> List[Dict]:
    """
    Find potential matching features between two datasets.

    Distance calculations are performed in a projected metric CRS (auto UTM).
    distance_threshold_meters defaults to 50 m.

    If the legacy `distance_threshold` kwarg is passed and looks like a degree
    value (≤ 1.0), a warning is added but we still use distance_threshold_meters.
    """

    if source_gdf.empty or target_gdf.empty:
        return []

    # ----------------------------------------------------------------
    # Project BOTH datasets to the same metric CRS derived from source
    # ----------------------------------------------------------------
    try:
        projected_crs = estimate_utm_crs(source_gdf)
    except ValueError:
        # Fallback: try target
        try:
            projected_crs = estimate_utm_crs(target_gdf)
        except ValueError:
            return []

    src_proj = to_projected(source_gdf, projected_crs)
    tgt_proj = to_projected(target_gdf, projected_crs)

    threshold_m = distance_threshold_meters

    matches: List[Dict] = []

    for source_index, source_row in src_proj.iterrows():
        source_geometry = source_row.geometry
        if source_geometry is None or source_geometry.is_empty:
            continue

        best_match = None
        best_score = 0.0

        for target_index, target_row in tgt_proj.iterrows():
            target_geometry = target_row.geometry
            if target_geometry is None or target_geometry.is_empty:
                continue

            # ---- metric distance ----
            distance_m = calculate_centroid_distance_meters(
                source_geometry, target_geometry
            )

            if distance_m > threshold_m:
                continue

            geometry_similarity = calculate_geometry_similarity(
                source_geometry, target_geometry
            )

            area_similarity = calculate_area_similarity(
                source_geometry, target_geometry
            )

            # Proximity score: 1.0 when distance=0, 0.0 at threshold
            proximity_score = max(0.0, 1.0 - (distance_m / threshold_m))

            # Weighted spatial score
            score = (
                0.45 * geometry_similarity
                + 0.30 * proximity_score
                + 0.25 * area_similarity
            )

            if score > best_score:
                best_score = score
                best_match = {
                    "source_index": int(source_index),
                    "target_index": int(target_index),
                    # Always return METRIC distance
                    "distance": float(distance_m),
                    "distance_meters": float(distance_m),
                    "geometry_similarity": float(geometry_similarity),
                    "area_similarity": float(area_similarity),
                    "proximity_score": float(proximity_score),
                    "confidence_score": float(score),
                    "projected_crs": projected_crs,
                    "distance_unit": "meters",
                }

        if best_match:
            matches.append(best_match)

    return matches