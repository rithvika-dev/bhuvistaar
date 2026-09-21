"""
Advanced conflict detection service.

Detects:
  - attribute_mismatch
  - geometry_conflict
  - identity_conflict (parcel_id, ULPIN, survey_number)
  - duplicate_feature
  - crs_inconsistency

Resolution statuses supported:
  - pending
  - accepted_source
  - accepted_target
  - merged
  - ignored

Never silently overwrites official records. All resolutions are auditable.
"""

import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.feature_match import FeatureMatch
from app.models.spatial_feature import SpatialFeature
from app.models.conflict import Conflict
from app.services.value_normalizer import is_missing_value, get_canonical_field_name


IDENTITY_FIELDS = {
    "parcel_id", "ulpin", "survey_number", "survey_no", "survey_num",
    "subdivision_number", "land_record_id", "source_record_id", "plot_number", "plot_no"
}


def detect_conflicts(
    db: Session,
    project_id: int
) -> dict:

    # Get all suggested feature matches for the project
    matches = (
        db.query(FeatureMatch)
        .filter(FeatureMatch.project_id == project_id)
        .all()
    )

    conflicts_found = []

    # Track target features to spot duplicate matches
    target_match_counts: Dict[int, List[int]] = {}
    for match in matches:
        target_match_counts.setdefault(match.target_feature_id, []).append(match.source_feature_id)

    # 1. Check duplicate feature assignments
    for target_id, source_ids in target_match_counts.items():
        if len(source_ids) > 1:
            conflict = Conflict(
                project_id=project_id,
                feature_id=target_id,
                conflict_type="duplicate_feature",
                description=f"Target feature {target_id} is matched to multiple source features: {source_ids}.",
                source_value=str(source_ids),
                target_value=str(target_id),
                confidence_score=0.85,
                resolution_status="pending"
            )
            db.add(conflict)
            conflicts_found.append({
                "feature_id": target_id,
                "conflict_type": "duplicate_feature",
                "description": conflict.description,
                "confidence": 0.85
            })

    for match in matches:
        source_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.source_feature_id).first()
        target_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.target_feature_id).first()

        if not source_feature or not target_feature:
            continue

        # 2. CRS inconsistency check
        source_srid = getattr(source_feature, "srid", 4326)
        target_srid = getattr(target_feature, "srid", 4326)
        if source_srid != target_srid:
            conflict = Conflict(
                project_id=project_id,
                feature_id=source_feature.id,
                conflict_type="crs_inconsistency",
                description=f"CRS/SRID mismatch between source (SRID {source_srid}) and target (SRID {target_srid}).",
                source_value=str(source_srid),
                target_value=str(target_srid),
                confidence_score=0.95,
                resolution_status="pending"
            )
            db.add(conflict)
            conflicts_found.append({
                "feature_id": source_feature.id,
                "conflict_type": "crs_inconsistency",
                "description": conflict.description,
                "confidence": 0.95
            })

        # 3. Geometry conflict (low similarity for matched features)
        geom_sim = match.geometry_similarity or 0.0
        if geom_sim < 0.60:
            conflict = Conflict(
                project_id=project_id,
                feature_id=source_feature.id,
                conflict_type="geometry_conflict",
                description=f"Matched features have low geometry similarity ({geom_sim:.2f}). Distance: {match.distance:.2f} m.",
                source_value=f"Source Feature {source_feature.id}",
                target_value=f"Target Feature {target_feature.id}",
                confidence_score=round(1.0 - geom_sim, 4),
                resolution_status="pending"
            )
            db.add(conflict)
            conflicts_found.append({
                "feature_id": source_feature.id,
                "conflict_type": "geometry_conflict",
                "description": conflict.description,
                "confidence": round(1.0 - geom_sim, 4)
            })

        # Parse properties
        try:
            source_properties = json.loads(source_feature.properties or "{}")
        except json.JSONDecodeError:
            source_properties = {}

        try:
            target_properties = json.loads(target_feature.properties or "{}")
        except json.JSONDecodeError:
            target_properties = {}

        # 4. Attribute mismatch & Identity conflict
        common_fields = set(source_properties.keys()).intersection(target_properties.keys())

        for field in common_fields:
            src_val = source_properties.get(field)
            tgt_val = target_properties.get(field)

            if is_missing_value(src_val) or is_missing_value(tgt_val):
                continue

            if str(src_val).strip().lower() == str(tgt_val).strip().lower():
                continue

            canonical_field = get_canonical_field_name(field)
            is_identity = canonical_field in IDENTITY_FIELDS or field.lower() in IDENTITY_FIELDS
            conflict_type = "identity_conflict" if is_identity else "attribute_mismatch"

            conflict_conf = max(0.0, min(1.0, 1.0 - (match.final_confidence_score or 0.5)))

            conflict = Conflict(
                project_id=project_id,
                feature_id=source_feature.id,
                conflict_type=conflict_type,
                description=f"{'Identity' if is_identity else 'Attribute'} '{field}' mismatch between source ('{src_val}') and target ('{tgt_val}').",
                source_value=str(src_val),
                target_value=str(tgt_val),
                confidence_score=conflict_conf,
                resolution_status="pending"
            )
            db.add(conflict)
            conflicts_found.append({
                "feature_id": source_feature.id,
                "field": field,
                "conflict_type": conflict_type,
                "source_value": src_val,
                "target_value": tgt_val,
                "confidence": conflict_conf
            })

    db.commit()

    return {
        "status": "completed",
        "project_id": project_id,
        "conflicts_found": len(conflicts_found),
        "conflicts": conflicts_found
    }


def resolve_conflict(
    db: Session,
    conflict_id: int,
    resolution_status: str,
    resolution_notes: Optional[str] = None,
    user_id: Optional[int] = None
) -> dict:

    allowed_statuses = {"accepted_source", "accepted_target", "merged", "ignored"}
    if resolution_status not in allowed_statuses:
        raise ValueError(f"Invalid resolution_status '{resolution_status}'. Allowed: {allowed_statuses}")

    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    if not conflict:
        raise ValueError("Conflict not found")

    conflict.resolution_status = resolution_status
    conflict.resolution_notes = resolution_notes
    db.commit()
    db.refresh(conflict)

    # Audit logging
    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=user_id,
        project_id=conflict.project_id,
        action="conflict_resolved",
        entity_type="conflict",
        entity_id=conflict.id,
        description=f"Conflict {conflict_id} resolved as '{resolution_status}'"
    )

    return {
        "status": "success",
        "conflict_id": conflict.id,
        "resolution_status": conflict.resolution_status,
        "resolution_notes": conflict.resolution_notes
    }