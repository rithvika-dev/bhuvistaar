"""
Version-based and Feature-pair Change Detection Service.

Calculates:
  - distance (in meters)
  - area_change (in m²)
  - geometry_change score
  - attribute_change score
  - confidence score

Categorizes version changes into:
  - added
  - removed
  - geometry_modified
  - attributes_modified
  - both_modified
  - unchanged
"""

import json
from difflib import SequenceMatcher
from typing import Dict, List, Optional
import geopandas as gpd
from sqlalchemy.orm import Session
from shapely.geometry.base import BaseGeometry
from geoalchemy2.shape import to_shape

from app.models.spatial_feature import SpatialFeature
from app.models.change_detection import ChangeDetection
from app.gis.crs_utils import estimate_utm_crs, to_projected


def geometry_similarity(
    old_geometry: BaseGeometry,
    new_geometry: BaseGeometry
) -> float:

    if old_geometry is None or new_geometry is None:
        return 0.0

    if old_geometry.is_empty or new_geometry.is_empty:
        return 0.0

    try:
        intersection = old_geometry.intersection(new_geometry)
        union = old_geometry.union(new_geometry)
    except Exception:
        return 0.0

    if union.is_empty or union.area == 0:
        return 0.0

    return float(intersection.area / union.area)


def attribute_similarity(
    old_attributes: dict,
    new_attributes: dict
) -> float:

    if not old_attributes and not new_attributes:
        return 1.0

    common_fields = set(old_attributes.keys()).intersection(
        set(new_attributes.keys())
    )

    if not common_fields:
        return 0.0

    scores = []

    for field in common_fields:
        old_value = str(old_attributes.get(field, ""))
        new_value = str(new_attributes.get(field, ""))

        if old_value == new_value:
            scores.append(1.0)
        else:
            scores.append(
                SequenceMatcher(
                    None,
                    old_value.lower(),
                    new_value.lower()
                ).ratio()
            )

    return sum(scores) / len(scores)


def detect_feature_change(
    old_feature: SpatialFeature,
    new_feature: SpatialFeature
) -> dict:

    try:
        old_attributes = json.loads(old_feature.properties) if old_feature.properties else {}
    except Exception:
        old_attributes = {}

    try:
        new_attributes = json.loads(new_feature.properties) if new_feature.properties else {}
    except Exception:
        new_attributes = {}

    old_geom = to_shape(old_feature.geometry) if hasattr(old_feature.geometry, "desc") else old_feature.geometry
    new_geom = to_shape(new_feature.geometry) if hasattr(new_feature.geometry, "desc") else new_feature.geometry

    geom_score = geometry_similarity(old_geom, new_geom)
    attr_score = attribute_similarity(old_attributes, new_attributes)

    similarity_score = (geom_score * 0.6) + (attr_score * 0.4)
    change_score = 1.0 - similarity_score

    if geom_score < 0.8 and attr_score < 0.8:
        change_type = "both_modified"
    elif geom_score < 0.8:
        change_type = "geometry_modified"
    elif attr_score < 0.8:
        change_type = "attributes_modified"
    else:
        change_type = "unchanged"

    description = (
        f"Geometry similarity: {geom_score:.3f}; "
        f"Attribute similarity: {attr_score:.3f}; "
        f"Change score: {change_score:.3f}"
    )

    return {
        "change_type": change_type,
        "description": description,
        "change_score": round(change_score, 4),
        "geometry_similarity": round(geom_score, 4),
        "attribute_similarity": round(attr_score, 4)
    }


def detect_changes_between_features(
    db: Session,
    project_id: int,
    old_feature_id: int,
    new_feature_id: int
) -> dict:

    old_feature = db.query(SpatialFeature).filter(SpatialFeature.id == old_feature_id).first()
    new_feature = db.query(SpatialFeature).filter(SpatialFeature.id == new_feature_id).first()

    if not old_feature:
        raise ValueError("Old feature not found")

    if not new_feature:
        raise ValueError("New feature not found")

    result = detect_feature_change(old_feature, new_feature)

    change_record = ChangeDetection(
        project_id=project_id,
        old_feature_id=old_feature_id,
        new_feature_id=new_feature_id,
        change_type=result["change_type"],
        description=result["description"],
        change_score=result["change_score"],
        review_status="pending"
    )

    db.add(change_record)
    db.commit()
    db.refresh(change_record)

    return {
        "status": "completed",
        "change_detection_id": change_record.id,
        "project_id": project_id,
        "old_feature_id": old_feature_id,
        "new_feature_id": new_feature_id,
        "change_type": result["change_type"],
        "change_score": result["change_score"],
        "geometry_similarity": result["geometry_similarity"],
        "attribute_similarity": result["attribute_similarity"],
        "review_status": change_record.review_status
    }


def detect_changes_between_versions(
    db: Session,
    project_id: int,
    old_version_id: int,
    new_version_id: int
) -> dict:

    old_features = (
        db.query(SpatialFeature)
        .filter(SpatialFeature.dataset_version_id == old_version_id)
        .all()
    )

    new_features = (
        db.query(SpatialFeature)
        .filter(SpatialFeature.dataset_version_id == new_version_id)
        .all()
    )

    if not old_features and not new_features:
        return {
            "status": "completed",
            "project_id": project_id,
            "old_version_id": old_version_id,
            "new_version_id": new_version_id,
            "changes_summary": {"added": 0, "removed": 0, "geometry_modified": 0, "attributes_modified": 0, "both_modified": 0, "unchanged": 0},
            "changes": []
        }

    # Extract geometries & properties into GDFs for spatial matching in projected CRS
    old_geoms = [to_shape(f.geometry) for f in old_features]
    new_geoms = [to_shape(f.geometry) for f in new_features]

    old_gdf = gpd.GeoDataFrame([{"id": f.id, "code": f.feature_code} for f in old_features], geometry=old_geoms, crs="EPSG:4326")
    new_gdf = gpd.GeoDataFrame([{"id": f.id, "code": f.feature_code} for f in new_features], geometry=new_geoms, crs="EPSG:4326")

    # Project to metric CRS
    try:
        crs_code = estimate_utm_crs(old_gdf if not old_gdf.empty else new_gdf)
        old_proj = to_projected(old_gdf, crs_code)
        new_proj = to_projected(new_gdf, crs_code)
    except Exception:
        old_proj = old_gdf
        new_proj = new_gdf

    matched_old_ids = set()
    matched_new_ids = set()
    changes = []
    summary_counts = {"added": 0, "removed": 0, "geometry_modified": 0, "attributes_modified": 0, "both_modified": 0, "unchanged": 0}

    # 1. Match old features to new features spatially
    for old_idx, old_row in old_proj.iterrows():
        old_feat = old_features[old_idx]
        old_geom = old_row.geometry

        best_match_idx = None
        best_dist = float("inf")
        best_geom_sim = 0.0

        for new_idx, new_row in new_proj.iterrows():
            new_geom = new_row.geometry
            try:
                dist = old_geom.centroid.distance(new_geom.centroid)
                if dist <= 50.0 and dist < best_dist:
                    best_dist = dist
                    best_match_idx = new_idx
            except Exception:
                pass

        if best_match_idx is not None:
            new_feat = new_features[best_match_idx]
            matched_old_ids.add(old_feat.id)
            matched_new_ids.add(new_feat.id)

            change_detail = detect_feature_change(old_feat, new_feat)
            c_type = change_detail["change_type"]
            summary_counts[c_type] = summary_counts.get(c_type, 0) + 1

            new_g = new_proj.iloc[best_match_idx].geometry
            area_change = abs(new_g.area - old_geom.area)

            rec = ChangeDetection(
                project_id=project_id,
                old_feature_id=old_feat.id,
                new_feature_id=new_feat.id,
                change_type=c_type,
                description=f"Distance: {best_dist:.2f} m | Area diff: {area_change:.2f} m² | {change_detail['description']}",
                change_score=change_detail["change_score"],
                review_status="pending"
            )
            db.add(rec)
            changes.append({
                "old_feature_id": old_feat.id,
                "new_feature_id": new_feat.id,
                "change_type": c_type,
                "distance_meters": round(best_dist, 2),
                "area_change_m2": round(area_change, 2),
                "geometry_similarity": change_detail["geometry_similarity"],
                "attribute_similarity": change_detail["attribute_similarity"],
                "change_score": change_detail["change_score"]
            })

    # 2. Flag removed features (in old, not matched to new)
    for old_feat in old_features:
        if old_feat.id not in matched_old_ids:
            summary_counts["removed"] += 1
            rec = ChangeDetection(
                project_id=project_id,
                old_feature_id=old_feat.id,
                new_feature_id=None,
                change_type="removed",
                description="Feature existed in old version but has no match in new version.",
                change_score=1.0,
                review_status="pending"
            )
            db.add(rec)
            changes.append({
                "old_feature_id": old_feat.id,
                "new_feature_id": None,
                "change_type": "removed",
                "change_score": 1.0
            })

    # 3. Flag added features (in new, not matched to old)
    for new_feat in new_features:
        if new_feat.id not in matched_new_ids:
            summary_counts["added"] += 1
            rec = ChangeDetection(
                project_id=project_id,
                old_feature_id=None,
                new_feature_id=new_feat.id,
                change_type="added",
                description="Feature added in new version with no corresponding old feature.",
                change_score=1.0,
                review_status="pending"
            )
            db.add(rec)
            changes.append({
                "old_feature_id": None,
                "new_feature_id": new_feat.id,
                "change_type": "added",
                "change_score": 1.0
            })

    # Audit logging
    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=None,
        project_id=project_id,
        action="version_change_detection",
        entity_type="dataset_version",
        entity_id=new_version_id,
        description=f"Change detection between version {old_version_id} and {new_version_id}: {summary_counts}"
    )

    db.commit()

    return {
        "status": "completed",
        "project_id": project_id,
        "old_version_id": old_version_id,
        "new_version_id": new_version_id,
        "changes_summary": summary_counts,
        "total_changes": len(changes),
        "changes": changes
    }