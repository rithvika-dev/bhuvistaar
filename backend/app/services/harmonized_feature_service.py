import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models.attribute_mapping import AttributeMapping
from app.models.feature_match import FeatureMatch
from app.models.spatial_feature import SpatialFeature
from app.models.harmonized_feature import HarmonizedFeature
from app.models.conflict import Conflict
from app.models.validation_result import ValidationResult


def generate_harmonized_features(
    db: Session,
    project_id: int
) -> dict:

    # Get approved attribute mappings
    mappings = (
        db.query(AttributeMapping)
        .filter(
            AttributeMapping.project_id == project_id,
            AttributeMapping.mapping_status == "approved"
        )
        .all()
    )

    if not mappings:
        return {
            "status": "no_approved_mappings",
            "message": "No approved attribute mappings found. Harmonization requires approved attribute mappings.",
            "created_count": 0
        }

    # Get feature matches for the project
    matches = (
        db.query(FeatureMatch)
        .filter(FeatureMatch.project_id == project_id)
        .all()
    )

    if not matches:
        return {
            "status": "no_matches",
            "message": "No feature matches found for this project.",
            "created_count": 0
        }

    created_features = []

    for match in matches:
        source_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.source_feature_id).first()
        target_feature = db.query(SpatialFeature).filter(SpatialFeature.id == match.target_feature_id).first()

        if not source_feature or not target_feature:
            continue

        try:
            source_attributes = json.loads(source_feature.properties) if source_feature.properties else {}
        except Exception:
            source_attributes = {}

        try:
            target_attributes = json.loads(target_feature.properties) if target_feature.properties else {}
        except Exception:
            target_attributes = {}

        harmonized_attributes = {}

        # Apply approved attribute mappings
        applied_mappings = []
        for mapping in mappings:
            source_value = source_attributes.get(mapping.source_field)
            if source_value is not None:
                harmonized_attributes[mapping.target_field] = source_value
                applied_mappings.append({"source_field": mapping.source_field, "target_field": mapping.target_field, "source_value": source_value})
            elif mapping.target_field in target_attributes:
                harmonized_attributes[mapping.target_field] = target_attributes[mapping.target_field]

        # Preserve unmapped target attributes
        for key, value in target_attributes.items():
            if key not in harmonized_attributes:
                harmonized_attributes[key] = value

        # Retrieve conflicts & validation results for provenance
        conflicts = db.query(Conflict).filter(Conflict.feature_id == source_feature.id).all()
        validations = db.query(ValidationResult).filter(ValidationResult.feature_id == source_feature.id).all()

        # Build full provenance JSON
        provenance = {
            "source_dataset_id": source_feature.dataset_id,
            "target_dataset_id": target_feature.dataset_id,
            "source_feature_id": source_feature.id,
            "target_feature_id": target_feature.id,
            "match_id": match.id,
            "match_confidence": match.final_confidence_score,
            "applied_attribute_mappings": applied_mappings,
            "conflicts": [
                {"id": c.id, "type": c.conflict_type, "status": c.resolution_status} for c in conflicts
            ],
            "validations": [
                {"type": v.validation_type, "status": v.status, "severity": v.severity} for v in validations
            ],
            "final_approval_required": True
        }

        match_confidence = match.final_confidence_score if match.final_confidence_score is not None else 0.0
        mapping_scores = [m.confidence_score for m in mappings if m.confidence_score is not None]
        mapping_confidence = (sum(mapping_scores) / len(mapping_scores)) if mapping_scores else 0.0
        final_confidence = round((match_confidence * 0.6) + (mapping_confidence * 0.4), 4)

        harmonized_feature = HarmonizedFeature(
            project_id=project_id,
            feature_id=target_feature.id,
            match_id=match.id,
            feature_type=target_feature.feature_type or "land_parcel",
            geometry=target_feature.geometry,
            harmonized_attributes=json.dumps(harmonized_attributes, default=str),
            source_info=json.dumps(provenance, default=str),
            confidence_score=final_confidence,
            review_status="pending"  # Not final until approved
        )

        db.add(harmonized_feature)
        created_features.append(harmonized_feature)

    db.commit()

    return {
        "status": "completed",
        "project_id": project_id,
        "created_count": len(created_features),
        "message": f"{len(created_features)} harmonized features created successfully with complete provenance. Approval required."
    }


def review_harmonized_feature(
    db: Session,
    harmonized_feature_id: int,
    review_status: str,
    reviewer_id: Optional[int] = None,
    review_notes: Optional[str] = None
) -> dict:
    if review_status not in ("approved", "rejected", "pending"):
        raise ValueError("Invalid review status. Must be 'approved', 'rejected', or 'pending'.")

    feature = db.query(HarmonizedFeature).filter(HarmonizedFeature.id == harmonized_feature_id).first()
    if not feature:
        raise ValueError("Harmonized feature not found")

    feature.review_status = review_status
    db.commit()

    # Audit log
    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=reviewer_id,
        project_id=feature.project_id,
        action="harmonized_feature_reviewed",
        entity_type="harmonized_feature",
        entity_id=feature.id,
        description=f"Harmonized feature {feature.id} reviewed as '{review_status}'. Notes: {review_notes or 'None'}"
    )

    return {
        "status": "success",
        "harmonized_feature_id": feature.id,
        "review_status": feature.review_status,
        "is_final": feature.review_status == "approved"
    }