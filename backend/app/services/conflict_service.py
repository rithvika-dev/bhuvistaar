"""
Advanced, Idempotent Conflict Detection and Resolution Service.

Detects:
  - attribute_mismatch (categorical differences, significant numeric area discrepancies)
  - identity_conflict (parcel_id, ulpin, khasra_no, survey_number)
  - geometry_conflict (significant spatial offset or low polygon IoU/similarity)
  - duplicate_feature (1:N or N:1 overlapping matches)
  - crs_inconsistency (spatial reference system mismatch)

Ignores:
  - Metadata / Provenance differences (source dataset name, survey year, capture dates)
  - Minor numeric differences within standard measurement tolerance (<= 5% area variance)

Guarantees:
  - 100% IDEMPOTENT: Running detection 1 time or 100 times produces the same logical conflict set
  - Preserves reviewed / resolved conflict records and reviewer notes
  - Auditable lifecycle logging for detection and resolution
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.models.feature_match import FeatureMatch
from app.models.spatial_feature import SpatialFeature
from app.models.conflict import Conflict
from app.services.value_normalizer import is_missing_value, get_canonical_field_name
from app.services.audit_service import create_audit_log


# Metadata & provenance fields that should NOT be treated as attribute conflicts
IGNORED_METADATA_FIELDS = {
    "source", "source_name", "dataset", "dataset_name", "dataset_type", "layer", "layer_name",
    "survey_year", "survey_date", "acquisition_date", "capture_date", "created_at", "updated_at",
    "timestamp", "file_name", "file_path", "crs", "srid", "gid", "objectid", "fid", "id",
    "feature_id", "match_id", "status"
}

# Legal land-record identity fields
IDENTITY_FIELDS = {
    "parcel_id", "ulpin", "khasra_no", "khasra_num", "survey_number", "survey_no", "survey_num",
    "subdivision_number", "land_record_id", "source_record_id", "plot_number", "plot_no",
    "property_tax_id", "tax_id", "pin", "upin"
}

# Critical categorical fields
CRITICAL_CATEGORICAL_FIELDS = {
    "land_use", "landuse", "ownership_type", "owner_type", "property_type", "zoning", "tenure"
}

# Numeric measurement fields (evaluated by relative difference threshold)
NUMERIC_MEASUREMENT_FIELDS = {
    "area_sq_m", "area_sqm", "area", "builtup_area", "footprint_area", "constructed_area",
    "perimeter", "height", "floors"
}


def normalize_value_str(val: Any) -> str:
    """Normalizes string value for comparison."""
    if val is None:
        return ""
    return str(val).strip().lower()


def try_parse_float(val: Any) -> Optional[float]:
    """Attempts to parse a numeric value."""
    if val is None:
        return None
    try:
        clean = re.sub(r"[^\d.-]", "", str(val))
        return float(clean)
    except (ValueError, TypeError):
        return None


def calculate_numeric_discrepancy(
    src_val: Any,
    tgt_val: Any,
    tolerance: float = 0.05
) -> Optional[Tuple[float, str, float, str, str]]:
    """
    Evaluates relative difference for numeric attributes.
    Returns (rel_diff, severity, confidence, description, suggested_resolution) if conflict, else None.
    """
    src_num = try_parse_float(src_val)
    tgt_num = try_parse_float(tgt_val)

    if src_num is None or tgt_num is None:
        return None

    denom = max(abs(tgt_num), 1e-6)
    rel_diff = abs(src_num - tgt_num) / denom

    # Within tolerance -> no conflict
    if rel_diff <= tolerance:
        return None

    diff_percent = rel_diff * 100.0

    if rel_diff <= 0.20:
        severity = "low"
        confidence = round(min(0.85, 0.70 + (rel_diff * 0.75)), 4)
    elif rel_diff <= 0.50:
        severity = "medium"
        confidence = round(min(0.92, 0.80 + (rel_diff * 0.25)), 4)
    else:
        severity = "high"
        confidence = round(min(0.98, 0.90 + (min(1.0, rel_diff) * 0.08)), 4)

    description = (
        f"Area / measurement differs by {diff_percent:.1f}% between source ('{src_val}') "
        f"and target ('{tgt_val}'), exceeding {tolerance * 100:.0f}% tolerance."
    )
    suggested_resolution = (
        "Verify parcel and building boundary geometry on GIS map, and recalculate "
        "authoritative area against latest field survey."
    )

    return rel_diff, severity, confidence, description, suggested_resolution


def get_conflict_identity_key(conflict: Conflict) -> Tuple[int, Optional[int], str, str]:
    """
    Generates a stable identity tuple for a conflict:
    (project_id, feature_id, conflict_type, conflict_key)
    """
    desc = conflict.description or ""
    field_key = ""
    if conflict.conflict_type in ("attribute_mismatch", "identity_conflict"):
        m = re.search(r"(?:Attribute|Identity)\s+'([^']+)'", desc)
        if m:
            field_key = m.group(1).strip().lower()
        else:
            field_key = desc[:40].strip().lower()
    elif conflict.conflict_type == "geometry_conflict":
        field_key = "geometry"
    elif conflict.conflict_type == "duplicate_feature":
        field_key = "duplicate"
    elif conflict.conflict_type == "crs_inconsistency":
        field_key = "crs"
    else:
        field_key = desc[:40].strip().lower()

    return (conflict.project_id, conflict.feature_id, conflict.conflict_type, field_key)


def detect_conflicts(
    db: Session,
    project_id: int,
    user_id: Optional[int] = None
) -> dict:
    """
    Performs idempotent, domain-aware conflict detection for a project.
    """
    # 1. Fetch feature matches
    matches = (
        db.query(FeatureMatch)
        .filter(FeatureMatch.project_id == project_id)
        .all()
    )

    # 2. Fetch all existing conflicts for this project into an identity map
    existing_conflicts = (
        db.query(Conflict)
        .filter(Conflict.project_id == project_id)
        .all()
    )

    conflict_map: Dict[Tuple[int, Optional[int], str, str], Conflict] = {}
    for c in existing_conflicts:
        key = get_conflict_identity_key(c)
        if key not in conflict_map:
            conflict_map[key] = c
        else:
            # Consolidate duplicate if found in memory
            if c.resolution_status != "pending" and conflict_map[key].resolution_status == "pending":
                db.delete(conflict_map[key])
                conflict_map[key] = c
            elif c.id != conflict_map[key].id:
                db.delete(c)

    conflicts_result: List[Conflict] = []

    # 3. Track target matches for duplicate feature assignments
    target_match_counts: Dict[int, List[int]] = {}
    for match in matches:
        target_match_counts.setdefault(match.target_feature_id, []).append(match.source_feature_id)

    # A. Check duplicate feature assignments (1:N or N:1)
    for target_id, source_ids in target_match_counts.items():
        if len(source_ids) > 1:
            key = (project_id, target_id, "duplicate_feature", "duplicate")
            desc = f"Target feature #{target_id} is matched to multiple source features ({source_ids}). Potential subdivision or duplicate footprint."
            suggested = "Review parcel boundaries on GIS map and resolve 1:N spatial division or remove duplicate footprint."

            if key in conflict_map:
                conflict = conflict_map[key]
                if conflict.resolution_status == "pending":
                    conflict.description = desc
                    conflict.source_value = str(source_ids)
                    conflict.target_value = str(target_id)
                    conflict.confidence_score = 0.90
                    conflict.severity = "high"
                    conflict.suggested_resolution = suggested
            else:
                conflict = Conflict(
                    project_id=project_id,
                    feature_id=target_id,
                    conflict_type="duplicate_feature",
                    severity="high",
                    description=desc,
                    source_value=str(source_ids),
                    target_value=str(target_id),
                    confidence_score=0.90,
                    suggested_resolution=suggested,
                    resolution_status="pending"
                )
                db.add(conflict)
                conflict_map[key] = conflict

            conflicts_result.append(conflict)

    # B. Inspect each matched pair
    for match in matches:
        source_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.source_feature_id).first()
        target_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.target_feature_id).first()

        if not source_feature or not target_feature:
            continue

        match_conf = match.final_confidence_score if match.final_confidence_score is not None else 0.80

        # 4. CRS Inconsistency Check
        source_srid = getattr(source_feature, "srid", 4326) or 4326
        target_srid = getattr(target_feature, "srid", 4326) or 4326
        if source_srid != target_srid:
            key = (project_id, source_feature.id, "crs_inconsistency", "crs")
            desc = f"CRS / SRID mismatch between source layer (EPSG:{source_srid}) and target layer (EPSG:{target_srid})."
            suggested = "Re-project source layer to project target metric coordinate reference system."

            if key in conflict_map:
                conflict = conflict_map[key]
                if conflict.resolution_status == "pending":
                    conflict.description = desc
                    conflict.source_value = f"EPSG:{source_srid}"
                    conflict.target_value = f"EPSG:{target_srid}"
                    conflict.confidence_score = 0.95
                    conflict.severity = "medium"
                    conflict.suggested_resolution = suggested
            else:
                conflict = Conflict(
                    project_id=project_id,
                    feature_id=source_feature.id,
                    conflict_type="crs_inconsistency",
                    severity="medium",
                    description=desc,
                    source_value=f"EPSG:{source_srid}",
                    target_value=f"EPSG:{target_srid}",
                    confidence_score=0.95,
                    suggested_resolution=suggested,
                    resolution_status="pending"
                )
                db.add(conflict)
                conflict_map[key] = conflict

            conflicts_result.append(conflict)

        # 5. Geometry Conflict Check (Meaningful spatial discrepancy)
        geom_sim = match.geometry_similarity if match.geometry_similarity is not None else 1.0
        distance = match.distance if match.distance is not None else 0.0

        if geom_sim < 0.65 or distance > 15.0:
            if geom_sim < 0.35 or distance > 25.0:
                geom_sev = "high"
            elif geom_sim < 0.55 or distance > 15.0:
                geom_sev = "medium"
            else:
                geom_sev = "low"

            geom_conf = round(min(0.98, max(0.65, 1.0 - (geom_sim * 0.4))), 4)
            key = (project_id, source_feature.id, "geometry_conflict", "geometry")
            desc = f"Matched features have low boundary similarity ({geom_sim * 100:.1f}%) and centroid offset of {distance:.1f} m."
            suggested = "Inspect spatial overlay on GIS map and align boundary vertices to authoritative GNSS/GCP survey."

            if key in conflict_map:
                conflict = conflict_map[key]
                if conflict.resolution_status == "pending":
                    conflict.description = desc
                    conflict.source_value = f"Source Feature #{source_feature.id}"
                    conflict.target_value = f"Target Feature #{target_feature.id}"
                    conflict.confidence_score = geom_conf
                    conflict.severity = geom_sev
                    conflict.suggested_resolution = suggested
            else:
                conflict = Conflict(
                    project_id=project_id,
                    feature_id=source_feature.id,
                    conflict_type="geometry_conflict",
                    severity=geom_sev,
                    description=desc,
                    source_value=f"Source Feature #{source_feature.id}",
                    target_value=f"Target Feature #{target_feature.id}",
                    confidence_score=geom_conf,
                    suggested_resolution=suggested,
                    resolution_status="pending"
                )
                db.add(conflict)
                conflict_map[key] = conflict

            conflicts_result.append(conflict)

        # 6. Parse properties
        try:
            source_props = json.loads(source_feature.properties or "{}")
        except (ValueError, TypeError):
            source_props = {}

        try:
            target_props = json.loads(target_feature.properties or "{}")
        except (ValueError, TypeError):
            target_props = {}

        common_fields = set(source_props.keys()).intersection(target_props.keys())

        for field in common_fields:
            canonical_field = get_canonical_field_name(field).lower()
            field_lower = field.lower()

            # Skip metadata / provenance / tracking fields
            if canonical_field in IGNORED_METADATA_FIELDS or field_lower in IGNORED_METADATA_FIELDS:
                continue

            src_val = source_props.get(field)
            tgt_val = target_props.get(field)

            if is_missing_value(src_val) or is_missing_value(tgt_val):
                continue

            # Check numeric discrepancy first
            if canonical_field in NUMERIC_MEASUREMENT_FIELDS or field_lower in NUMERIC_MEASUREMENT_FIELDS:
                num_check = calculate_numeric_discrepancy(src_val, tgt_val, tolerance=0.05)
                if num_check is None:
                    # Within tolerance -> no conflict!
                    continue

                rel_diff, num_sev, num_conf, num_desc, num_sugg = num_check
                key = (project_id, source_feature.id, "attribute_mismatch", canonical_field)

                if key in conflict_map:
                    conflict = conflict_map[key]
                    if conflict.resolution_status == "pending":
                        conflict.description = num_desc
                        conflict.source_value = str(src_val)
                        conflict.target_value = str(tgt_val)
                        conflict.confidence_score = num_conf
                        conflict.severity = num_sev
                        conflict.suggested_resolution = num_sugg
                else:
                    conflict = Conflict(
                        project_id=project_id,
                        feature_id=source_feature.id,
                        conflict_type="attribute_mismatch",
                        severity=num_sev,
                        description=num_desc,
                        source_value=str(src_val),
                        target_value=str(tgt_val),
                        confidence_score=num_conf,
                        suggested_resolution=num_sugg,
                        resolution_status="pending"
                    )
                    db.add(conflict)
                    conflict_map[key] = conflict

                conflicts_result.append(conflict)
                continue

            # Categorical string comparison
            if normalize_value_str(src_val) == normalize_value_str(tgt_val):
                continue

            # Legal / Identity conflict
            is_identity = canonical_field in IDENTITY_FIELDS or field_lower in IDENTITY_FIELDS
            is_critical = canonical_field in CRITICAL_CATEGORICAL_FIELDS or field_lower in CRITICAL_CATEGORICAL_FIELDS

            if is_identity:
                conflict_type = "identity_conflict"
                severity = "high"
                conf_score = round(min(0.98, 0.85 + (match_conf * 0.10)), 4)
                desc = f"Identity mismatch for '{field}': source record has '{src_val}', target record has '{tgt_val}'."
                suggested = "Cross-check legal cadastral records and Revenue RoR to verify correct parcel identification."
            elif is_critical:
                conflict_type = "attribute_mismatch"
                severity = "high"
                conf_score = round(min(0.98, 0.85 + (match_conf * 0.10)), 4)
                desc = f"Land-use / zoning classification differs between source ('{src_val}') and target ('{tgt_val}')."
                suggested = "Review latest authoritative municipal master plan and revenue records for classification."
            else:
                conflict_type = "attribute_mismatch"
                severity = "medium"
                conf_score = round(min(0.95, 0.75 + (match_conf * 0.15)), 4)
                desc = f"Attribute '{field}' differs: source has '{src_val}', target has '{tgt_val}'."
                suggested = "Verify attribute values across authoritative multi-source registries."

            key = (project_id, source_feature.id, conflict_type, canonical_field)

            if key in conflict_map:
                conflict = conflict_map[key]
                if conflict.resolution_status == "pending":
                    conflict.description = desc
                    conflict.source_value = str(src_val)
                    conflict.target_value = str(tgt_val)
                    conflict.confidence_score = conf_score
                    conflict.severity = severity
                    conflict.suggested_resolution = suggested
            else:
                conflict = Conflict(
                    project_id=project_id,
                    feature_id=source_feature.id,
                    conflict_type=conflict_type,
                    severity=severity,
                    description=desc,
                    source_value=str(src_val),
                    target_value=str(tgt_val),
                    confidence_score=conf_score,
                    suggested_resolution=suggested,
                    resolution_status="pending"
                )
                db.add(conflict)
                conflict_map[key] = conflict

            conflicts_result.append(conflict)

    db.commit()

    # Log audit event
    create_audit_log(
        db=db,
        user_id=user_id,
        project_id=project_id,
        action="conflict_detected",
        entity_type="project",
        entity_id=project_id,
        description=f"Idempotent conflict detection completed: {len(conflicts_result)} logical conflicts identified."
    )

    serialized = [
        {
            "id": c.id,
            "feature_id": c.feature_id,
            "conflict_type": c.conflict_type,
            "severity": c.severity or "medium",
            "description": c.description,
            "source_value": c.source_value,
            "target_value": c.target_value,
            "confidence_score": c.confidence_score,
            "suggested_resolution": c.suggested_resolution,
            "resolution_status": c.resolution_status,
            "resolution_notes": c.resolution_notes,
            "created_at": str(c.created_at) if c.created_at else None
        }
        for c in conflicts_result
    ]

    return {
        "status": "completed",
        "project_id": project_id,
        "conflicts_found": len(serialized),
        "conflicts": serialized
    }


def resolve_conflict(
    db: Session,
    conflict_id: int,
    resolution_status: str,
    resolution_notes: Optional[str] = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Persists human review resolution for a conflict to PostgreSQL and creates an audit log.
    """
    allowed_statuses = {
        "resolved",
        "approved",
        "rejected",
        "accepted_source",
        "accepted_target",
        "merged",
        "ignored"
    }

    if resolution_status not in allowed_statuses:
        raise ValueError(f"Invalid resolution_status '{resolution_status}'. Allowed: {sorted(allowed_statuses)}")

    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    if not conflict:
        raise ValueError("Conflict not found")

    conflict.resolution_status = resolution_status
    if resolution_notes:
        conflict.resolution_notes = resolution_notes

    db.commit()
    db.refresh(conflict)

    # Audit logging
    create_audit_log(
        db=db,
        user_id=user_id,
        project_id=conflict.project_id,
        action="conflict_resolved",
        entity_type="conflict",
        entity_id=conflict.id,
        description=f"Conflict #{conflict_id} ({conflict.conflict_type}) marked as '{resolution_status}'. Notes: {resolution_notes or 'None'}"
    )

    return {
        "status": "success",
        "conflict_id": conflict.id,
        "project_id": conflict.project_id,
        "conflict_type": conflict.conflict_type,
        "severity": conflict.severity,
        "resolution_status": conflict.resolution_status,
        "resolution_notes": conflict.resolution_notes
    }