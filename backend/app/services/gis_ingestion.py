import os
import geopandas as gpd

from app.gis.inspector import inspect_vector_file
from app.gis.crs import normalize_crs


def ingest_vector_dataset(file_path: str) -> dict:
    """
    Read, inspect, and normalize a vector geospatial dataset.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    # Read vector dataset
    gdf = gpd.read_file(file_path)

    if gdf.empty:
        raise ValueError("The uploaded dataset contains no features")

    # Inspect original dataset
    inspection = inspect_vector_file(file_path)

    # CRS is required for automatic normalization
    if gdf.crs is None:
        return {
            "status": "crs_missing",
            "message": "Dataset does not contain a CRS. Georeferencing is required.",
            "inspection": inspection
        }

    original_crs = str(gdf.crs)

    # Convert to common BhuVistaar CRS
    normalized_gdf = normalize_crs(gdf)

    return {
        "status": "ready",
        "feature_count": len(normalized_gdf),
        "original_crs": original_crs,
        "normalized_crs": str(normalized_gdf.crs),
        "geometry_types": [
            geometry_type
            for geometry_type in normalized_gdf.geometry.geom_type.dropna().unique()
        ],
        "columns": list(normalized_gdf.columns),
        "bounds": {
            "min_x": float(normalized_gdf.total_bounds[0]),
            "min_y": float(normalized_gdf.total_bounds[1]),
            "max_x": float(normalized_gdf.total_bounds[2]),
            "max_y": float(normalized_gdf.total_bounds[3])
        }
    }