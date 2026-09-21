"""
Raster processor: reprojection, OpenCV-based edge detection and candidate feature extraction.

IMPORTANT DESIGN NOTE:
The OpenCV processing here (Canny edge detection + contour extraction) provides a
*candidate* set of shapes that may correspond to buildings, roads or parcels.
It is NOT a trained building/road extraction AI model.
Future versions can replace or supplement this classical CV module with a proper
segmentation model (e.g. SegNet, U-Net) by swapping the extract_raster_features() logic.
"""

import os
import tempfile
from typing import Optional

import numpy as np
import cv2
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
from shapely.geometry import shape, mapping
import json


def reproject_raster(
    input_path: str,
    output_path: str,
    target_crs: str = "EPSG:4326"
) -> dict:
    """
    Reprojects a raster file to the target CRS.
    Writes the reprojected file to output_path.
    Never modifies the original file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input raster not found: {input_path}")

    with rasterio.open(input_path) as src:
        dst_crs = CRS.from_user_input(target_crs)

        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with rasterio.open(output_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )

    return {
        "status": "success",
        "input_path": input_path,
        "output_path": output_path,
        "target_crs": target_crs
    }


def extract_raster_features(
    file_path: str,
    band_index: int = 1,
    canny_low: int = 50,
    canny_high: int = 150
) -> dict:
    """
    Extract candidate boundary features from a raster using OpenCV edge detection.

    PROTOTYPE WARNING:
    This uses classical computer vision (Canny edges + contour finding).
    It produces candidate shapes but is NOT a trained AI model.
    Results require human review before use in official land records.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with rasterio.open(file_path) as src:
        transform = src.transform
        crs = str(src.crs) if src.crs else None

        if band_index > src.count:
            raise ValueError(f"Band {band_index} not available. File has {src.count} bands.")

        data = src.read(band_index)

    # Normalize to uint8 for OpenCV
    data_min, data_max = data.min(), data.max()
    if data_max == data_min:
        raise ValueError("Band has no variation; cannot extract features.")

    data_norm = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)

    # Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(data_norm, (5, 5), 0)

    # Canny edge detection
    edges = cv2.Canny(blurred, canny_low, canny_high)

    # Find contours from edge map
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Convert pixel contours to geographic coordinates
    candidate_features = []
    for contour in contours:
        if len(contour) < 4:
            continue

        # Convert pixel coords to geo coords using affine transform
        geo_coords = []
        for point in contour:
            px, py = point[0][0], point[0][1]
            gx = transform.c + px * transform.a + py * transform.b
            gy = transform.f + px * transform.d + py * transform.e
            geo_coords.append([gx, gy])

        if len(geo_coords) >= 4:
            candidate_features.append({
                "type": "candidate_polygon",
                "coordinates": geo_coords,
                "pixel_area": cv2.contourArea(contour),
                "requires_review": True
            })

    return {
        "status": "completed",
        "file_path": file_path,
        "crs": crs,
        "band_used": band_index,
        "edge_detection": {
            "method": "Canny",
            "low_threshold": canny_low,
            "high_threshold": canny_high
        },
        "candidate_feature_count": len(candidate_features),
        "candidate_features": candidate_features[:100],  # cap output
        "prototype_warning": (
            "These are candidate boundaries from classical edge detection. "
            "They are NOT ground-truth features. Human review is mandatory."
        )
    }
