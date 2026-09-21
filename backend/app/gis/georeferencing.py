import geopandas as gpd
from shapely.geometry import box


def estimate_georeferencing(gdf: gpd.GeoDataFrame) -> dict:
    """
    Provide a basic georeferencing assessment for datasets
    whose CRS information is missing.
    """

    if gdf.empty:
        raise ValueError("Dataset contains no features")

    bounds = gdf.total_bounds

    min_x, min_y, max_x, max_y = bounds

    extent = box(min_x, min_y, max_x, max_y)

    return {
        "status": "georeferencing_required",
        "message": (
            "CRS information is missing. "
            "Ground control points or source metadata are required "
            "for accurate georeferencing."
        ),
        "source_bounds": {
            "min_x": float(min_x),
            "min_y": float(min_y),
            "max_x": float(max_x),
            "max_y": float(max_y)
        },
        "source_extent_area": float(extent.area),
        "requires_ground_control_points": True,
        "recommended_method": "control_point_transformation"
    }


def apply_georeferencing(
    gdf: gpd.GeoDataFrame,
    source_crs: str
) -> gpd.GeoDataFrame:
    """
    Assign the known source CRS to a dataset.

    This does not transform coordinates.
    It only defines the coordinate reference system.
    """

    if gdf.empty:
        raise ValueError("Dataset contains no features")

    if not source_crs:
        raise ValueError("Source CRS is required")

    gdf = gdf.copy()

    gdf = gdf.set_crs(source_crs, allow_override=True)

    return gdf


import numpy as np
import cv2
import shapely.affinity
import math

def calculate_transform_matrix(gcps, method="affine"):
    if len(gcps) < 3:
        raise ValueError("At least 3 GCPs are required")
        
    src_pts = np.array([[gcp.source_x, gcp.source_y] for gcp in gcps], dtype=np.float32)
    dst_pts = np.array([[gcp.target_x, gcp.target_y] for gcp in gcps], dtype=np.float32)

    if method == "affine":
        matrix, _ = cv2.estimateAffine2D(src_pts, dst_pts)
    elif method == "similarity":
        matrix, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)
    else:
        raise ValueError(f"Unsupported transformation method: {method}")
    
    if matrix is None:
        raise ValueError("Could not compute transformation matrix from provided GCPs")
    
    return matrix

def transform_with_gcps(gdf: gpd.GeoDataFrame, gcps, method="affine"):
    if gdf.empty:
        raise ValueError("Dataset contains no features")
        
    matrix = calculate_transform_matrix(gcps, method)
    
    # cv2 matrix is:
    # [a, b, tx]
    # [c, d, ty]
    # shapely affine_transform expects [a, b, c, d, tx, ty]
    a, b, tx = matrix[0]
    c, d, ty = matrix[1]
    shapely_matrix = [a, b, c, d, tx, ty]
    
    transformed_gdf = gdf.copy()
    transformed_gdf.geometry = transformed_gdf.geometry.apply(
        lambda geom: shapely.affinity.affine_transform(geom, shapely_matrix) if geom is not None else None
    )
    
    # Set the new CRS based on the GCPs
    target_crs = gcps[0].target_crs if gcps else "EPSG:4326"
    transformed_gdf = transformed_gdf.set_crs(target_crs, allow_override=True)
    
    return transformed_gdf, matrix

def calculate_residuals(gcps, matrix):
    if not gcps or matrix is None:
        return 0.0, []
        
    residuals = []
    for gcp in gcps:
        src = np.array([gcp.source_x, gcp.source_y, 1.0])
        pred = matrix.dot(src)
        err = math.sqrt((pred[0] - gcp.target_x)**2 + (pred[1] - gcp.target_y)**2)
        residuals.append(err)
        
    rmse = math.sqrt(sum(r**2 for r in residuals) / len(residuals))
    return rmse, residuals

def validate_gcps(gcps):
    errors = []
    is_valid = True
    
    if len(gcps) < 3:
        errors.append("At least 3 GCPs are required for affine transformation.")
        is_valid = False
        
    # Check for duplicate source points
    src_points = set((gcp.source_x, gcp.source_y) for gcp in gcps)
    if len(src_points) < len(gcps):
        errors.append("Duplicate source coordinates found.")
        is_valid = False
        
    return {
        "is_valid": is_valid,
        "point_count": len(gcps),
        "minimum_required": 3,
        "has_duplicates": len(src_points) < len(gcps),
        "is_collinear": False, # simplified for now
        "errors": errors
    }