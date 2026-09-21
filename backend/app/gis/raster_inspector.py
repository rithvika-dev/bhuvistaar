import os
import numpy as np
import rasterio
from rasterio.crs import CRS


def inspect_raster_file(file_path: str) -> dict:
    """
    Inspect a raster geospatial dataset and return comprehensive metadata.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with rasterio.open(file_path) as dataset:

        bounds = dataset.bounds
        transform = dataset.transform

        # Band statistics
        band_stats = []
        for band_idx in range(1, dataset.count + 1):
            try:
                data = dataset.read(band_idx, masked=True)
                band_stats.append({
                    "band": band_idx,
                    "min": float(np.min(data)) if data.count() > 0 else None,
                    "max": float(np.max(data)) if data.count() > 0 else None,
                    "mean": float(np.mean(data)) if data.count() > 0 else None,
                    "nodata_count": int(np.sum(data.mask)) if hasattr(data, 'mask') else 0
                })
            except Exception:
                band_stats.append({"band": band_idx, "error": "Could not read band statistics"})

        # Resolution in metres (approximate, only valid for projected CRS)
        res_m = None
        if dataset.crs:
            try:
                crs_obj = CRS.from_user_input(dataset.crs)
                if crs_obj.is_projected:
                    res_m = {"x_m": float(dataset.res[0]), "y_m": float(dataset.res[1])}
            except Exception:
                pass

        raw_metadata = dict(dataset.tags())
        raster_type = classify_raster_type(
            file_path=file_path,
            band_count=dataset.count,
            dtype=str(dataset.dtypes[0]),
            metadata=raw_metadata
        )

        return {
            "width": dataset.width,
            "height": dataset.height,
            "band_count": dataset.count,
            "crs": str(dataset.crs) if dataset.crs else None,
            "driver": dataset.driver,
            "dtype": str(dataset.dtypes[0]),
            "nodata": dataset.nodata,
            "bounds": {
                "min_x": float(bounds.left),
                "min_y": float(bounds.bottom),
                "max_x": float(bounds.right),
                "max_y": float(bounds.top)
            },
            "resolution": {
                "x": float(dataset.res[0]),
                "y": float(dataset.res[1])
            },
            "resolution_meters": res_m,
            "transform": list(transform)[:6],
            "band_statistics": band_stats,
            "metadata": raw_metadata,
            "raster_type": raster_type
        }


def classify_raster_type(file_path: str, band_count: int, dtype: str, metadata: dict) -> str:
    """
    Heuristically classify the raster type: ORI, DSM, DTM, drone_imagery, or generic_raster.
    This is a best-effort classification based on filename patterns and metadata.
    """
    name_lower = os.path.basename(file_path).lower()

    # Check filename patterns first
    if any(k in name_lower for k in ["dsm", "digital_surface"]):
        return "DSM"
    if any(k in name_lower for k in ["dtm", "dem", "digital_terrain", "digital_elevation"]):
        return "DTM"
    if any(k in name_lower for k in ["ori", "ortho", "orthophoto"]):
        return "ORI"
    if any(k in name_lower for k in ["drone", "uav", "uas"]):
        return "drone_imagery"

    # Check metadata tags
    description = metadata.get("DESCRIPTION", "").lower() + metadata.get("description", "").lower()
    if "dsm" in description or "surface model" in description:
        return "DSM"
    if "dtm" in description or "terrain model" in description or "dem" in description:
        return "DTM"
    if "ortho" in description:
        return "ORI"

    # Fallback by band count and dtype
    if band_count == 1 and dtype in ("float32", "float64", "int16", "int32"):
        return "elevation_raster"  # likely DSM/DTM, not enough info
    if band_count >= 3:
        return "imagery"

    return "generic_raster"