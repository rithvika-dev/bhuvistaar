import os

import geopandas as gpd


def inspect_vector_file(file_path: str) -> dict:
    """
    Inspect a vector geospatial dataset.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    gdf = gpd.read_file(file_path)

    geometry_types = []

    if not gdf.empty:
        geometry_types = [
            geometry_type
            for geometry_type in gdf.geometry.geom_type.dropna().unique()
        ]

    bounds = None

    if not gdf.empty:
        min_x, min_y, max_x, max_y = gdf.total_bounds

        bounds = {
            "min_x": float(min_x),
            "min_y": float(min_y),
            "max_x": float(max_x),
            "max_y": float(max_y)
        }

    return {
        "feature_count": len(gdf),
        "crs": str(gdf.crs) if gdf.crs else None,
        "geometry_types": geometry_types,
        "columns": list(gdf.columns),
        "bounds": bounds
    }