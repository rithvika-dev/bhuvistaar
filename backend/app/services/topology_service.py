"""
Advanced topology validation service.

Extends the existing basic checks (invalid/duplicate geometry) with:
  - Self-intersection detection
  - Gap detection (for polygon datasets)
  - Overlap detection (for polygon datasets)
  - Missing geometry
  - Unexpected geometry type
  - Disconnected features

IMPORTANT:
  - Correction suggestions are NON-DESTRUCTIVE. They are stored as text
    recommendations only. The original source data is never modified.
  - Severity levels: info | warning | error | critical
"""

import os
from typing import List, Dict, Optional

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.validation_result import ValidationResult
from app.gis.crs_utils import to_projected


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _severity_for_type(validation_type: str) -> str:
    mapping = {
        "missing_geometry":      "critical",
        "invalid_geometry":      "error",
        "self_intersection":     "error",
        "overlap":               "error",
        "duplicate_geometry":    "warning",
        "gap":                   "warning",
        "unexpected_geom_type":  "warning",
        "disconnected_feature":  "info",
    }
    return mapping.get(validation_type, "warning")


def _add_result(
    db: Session,
    results: List[Dict],
    project_id: int,
    validation_type: str,
    message: str,
    feature_index: Optional[int] = None,
    extra: Optional[Dict] = None,
    suggestion: Optional[str] = None,
) -> None:
    severity = _severity_for_type(validation_type)

    full_message = message
    if suggestion:
        full_message += f" | Suggestion: {suggestion}"

    result = ValidationResult(
        project_id=project_id,
        feature_id=None,
        validation_type=validation_type,
        status="failed",
        severity=severity,
        message=full_message,
        confidence_score=1.0,
    )
    db.add(result)

    entry: Dict = {
        "validation_type": validation_type,
        "severity": severity,
        "message": message,
        "suggestion": suggestion,
    }
    if feature_index is not None:
        entry["feature_index"] = int(feature_index)
    if extra:
        entry.update(extra)

    results.append(entry)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_invalid_and_missing(gdf: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """Check for None, empty and geometrically invalid features."""
    for index, row in gdf.iterrows():
        geom = row.geometry

        if geom is None:
            _add_result(db, results, project_id, "missing_geometry",
                        f"Feature {index} has no geometry.",
                        feature_index=index,
                        suggestion="Re-inspect source file for null geometry rows.")
            continue

        if geom.is_empty:
            _add_result(db, results, project_id, "invalid_geometry",
                        f"Feature {index} has empty geometry.",
                        feature_index=index,
                        suggestion="Remove or repair empty geometry records.")
            continue

        if not geom.is_valid:
            _add_result(db, results, project_id, "invalid_geometry",
                        f"Feature {index} ({geom.geom_type}) is geometrically invalid.",
                        feature_index=index,
                        extra={"geom_type": geom.geom_type},
                        suggestion="Apply ST_MakeValid or buffer(0) to repair geometry.")
            continue

        # Only valid non-empty geometries are eligible for further checks
        valid_indices.add(index)


def check_self_intersections(gdf: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """Detect self-intersecting ring geometries (polygons)."""
    for index, row in gdf.iterrows():
        if index not in valid_indices:
            continue
        geom = row.geometry
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        # A self-intersecting polygon is reported as invalid by Shapely,
        # but some edge cases (bowtie polygons) may slip through.
        # Check exterior ring explicitly.
        try:
            exterior = geom.exterior if hasattr(geom, "exterior") else None
            if exterior and not exterior.is_simple:
                _add_result(db, results, project_id, "self_intersection",
                            f"Feature {index} exterior ring self-intersects.",
                            feature_index=index,
                            suggestion="Use ST_MakeValid to resolve self-intersections.")
        except Exception:
            pass


def check_duplicates(gdf: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """Check for exactly identical geometries."""
    indices = [i for i in gdf.index if i in valid_indices]
    for pos_a in range(len(indices)):
        i = indices[pos_a]
        geom_a = gdf.loc[i].geometry
        for pos_b in range(pos_a + 1, len(indices)):
            j = indices[pos_b]
            geom_b = gdf.loc[j].geometry
            if geom_a.equals(geom_b):
                _add_result(db, results, project_id, "duplicate_geometry",
                            f"Features {i} and {j} have identical geometries.",
                            feature_index=i,
                            extra={"duplicate_feature_index": int(j)},
                            suggestion="Remove duplicate or verify if two records legitimately describe the same parcel.")


def check_overlaps(gdf_proj: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """
    Detect overlapping polygons. Uses the projected GDF for area accuracy.
    Only checks Polygon / MultiPolygon datasets.
    """
    poly_mask = gdf_proj.geom_type.isin(["Polygon", "MultiPolygon"])
    if not poly_mask.any():
        return

    poly_gdf = gdf_proj[poly_mask]
    indices = [i for i in poly_gdf.index if i in valid_indices]

    for pos_a in range(len(indices)):
        i = indices[pos_a]
        geom_a = poly_gdf.loc[i].geometry
        for pos_b in range(pos_a + 1, len(indices)):
            j = indices[pos_b]
            geom_b = poly_gdf.loc[j].geometry
            try:
                if geom_a.intersects(geom_b):
                    overlap = geom_a.intersection(geom_b)
                    if not overlap.is_empty and overlap.area > 0.01:  # > 0.01 m²
                        _add_result(db, results, project_id, "overlap",
                                    f"Features {i} and {j} overlap by {overlap.area:.2f} m².",
                                    feature_index=i,
                                    extra={
                                        "overlapping_feature_index": int(j),
                                        "overlap_area_m2": round(float(overlap.area), 4),
                                    },
                                    suggestion="Investigate boundary dispute. Use conflict resolution workflow.")
            except Exception:
                pass


def check_gaps(gdf_proj: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """
    Detect gaps between adjacent polygons by comparing union with convex hull.
    Only meaningful for polygon datasets covering a continuous area.
    """
    poly_mask = gdf_proj.geom_type.isin(["Polygon", "MultiPolygon"])
    if not poly_mask.any():
        return

    valid_geoms = [
        gdf_proj.loc[i].geometry
        for i in gdf_proj[poly_mask].index
        if i in valid_indices
    ]

    if len(valid_geoms) < 2:
        return

    try:
        unioned = unary_union(valid_geoms)
        convex = unioned.convex_hull

        if not unioned.is_valid or not convex.is_valid:
            return

        gap_area = convex.area - unioned.area

        # Only report if gap is more than 0.1% of total union area
        if unioned.area > 0 and (gap_area / unioned.area) > 0.001:
            _add_result(db, results, project_id, "gap",
                        f"Potential gaps detected. Estimated gap area: {gap_area:.2f} m² "
                        f"({100 * gap_area / convex.area:.2f}% of convex hull).",
                        suggestion=(
                            "Inspect boundaries between adjacent parcels. "
                            "Gaps may indicate missing parcels or digitization errors."
                        ))
    except Exception:
        pass


def check_unexpected_geometry_type(gdf: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """Warn when a dataset contains mixed geometry types unexpectedly."""
    geom_types = set()
    for index in valid_indices:
        if index in gdf.index:
            geom_types.add(gdf.loc[index].geometry.geom_type)

    if len(geom_types) > 1:
        _add_result(db, results, project_id, "unexpected_geom_type",
                    f"Dataset contains mixed geometry types: {sorted(geom_types)}.",
                    suggestion="Separate into single-type layers for cleaner harmonization.")


def check_disconnected_features(gdf_proj: gpd.GeoDataFrame, db, results, project_id, valid_indices):
    """
    Detect features that are entirely isolated (no neighbour within 100 m).
    Only informational — does not imply an error.
    """
    if len(valid_indices) < 2:
        return

    indices = [i for i in gdf_proj.index if i in valid_indices]
    ISOLATION_THRESHOLD_M = 100.0

    for i in indices:
        geom_i = gdf_proj.loc[i].geometry
        has_neighbour = False
        for j in indices:
            if i == j:
                continue
            geom_j = gdf_proj.loc[j].geometry
            try:
                if geom_i.centroid.distance(geom_j.centroid) < ISOLATION_THRESHOLD_M:
                    has_neighbour = True
                    break
            except Exception:
                pass

        if not has_neighbour:
            _add_result(db, results, project_id, "disconnected_feature",
                        f"Feature {i} has no neighbour within {ISOLATION_THRESHOLD_M} m.",
                        feature_index=i,
                        suggestion="Verify if this feature is intentionally isolated or a digitization outlier.")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def validate_dataset_topology(
    db: Session,
    project_id: int,
    dataset_id: int,
) -> dict:

    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.project_id == project_id)
        .first()
    )

    if not dataset:
        raise ValueError("Dataset not found")

    if not dataset.file_path:
        raise ValueError("Dataset has no uploaded file")

    if not os.path.exists(dataset.file_path):
        raise FileNotFoundError("Dataset file does not exist")

    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )

    if not version:
        raise ValueError("Dataset has not been processed yet")

    gdf = gpd.read_file(dataset.file_path)
    if gdf.empty:
        raise ValueError("Dataset contains no features")

    # Project to metric CRS for area/distance checks
    try:
        gdf_proj = to_projected(gdf)
    except Exception:
        gdf_proj = gdf  # fallback: use as-is

    validation_results: List[Dict] = []
    valid_indices: set = set()

    # --- Run all checks ---
    check_invalid_and_missing(gdf, db, validation_results, project_id, valid_indices)
    check_self_intersections(gdf, db, validation_results, project_id, valid_indices)
    check_duplicates(gdf, db, validation_results, project_id, valid_indices)
    check_overlaps(gdf_proj, db, validation_results, project_id, valid_indices)
    check_gaps(gdf_proj, db, validation_results, project_id, valid_indices)
    check_unexpected_geometry_type(gdf, db, validation_results, project_id, valid_indices)
    check_disconnected_features(gdf_proj, db, validation_results, project_id, valid_indices)

    db.commit()

    # Summary counts by severity
    by_severity: Dict[str, int] = {}
    for r in validation_results:
        sev = r.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "status": "completed",
        "project_id": project_id,
        "dataset_id": dataset_id,
        "feature_count": len(gdf),
        "valid_feature_count": len(valid_indices),
        "validation_count": len(validation_results),
        "by_severity": by_severity,
        "validations": validation_results,
        "note": (
            "Suggestions are non-destructive recommendations only. "
            "Source data has not been modified."
        ),
    }