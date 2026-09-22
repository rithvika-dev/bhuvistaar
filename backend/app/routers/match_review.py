import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feature_match import FeatureMatch
from app.models.harmonized_feature import HarmonizedFeature
from app.models.spatial_feature import SpatialFeature
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.audit_service import create_audit_log
from app.ai.confidence_service import build_confidence_result


router = APIRouter(
    prefix="/match-results",
    tags=["Feature Match Review"]
)


class MatchReviewRequest(BaseModel):
    match_status: str
    review_notes: str | None = None


@router.put("/{match_id}/review")
def review_match(
    match_id: int,
    request: MatchReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Find match
    # --------------------------------------------------
    match = (
        db.query(FeatureMatch)
        .filter(FeatureMatch.id == match_id)
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Feature match not found"
        )

    # --------------------------------------------------
    # 2. Find project
    # --------------------------------------------------
    project = (
        db.query(Project)
        .filter(Project.id == match.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # --------------------------------------------------
    # 3. Check project ownership
    # --------------------------------------------------
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this match"
        )

    # --------------------------------------------------
    # 4. Validate review status
    # --------------------------------------------------
    allowed_statuses = {
        "approved",
        "rejected"
    }

    if request.match_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid match status. "
                "Use approved or rejected."
            )
        )

    # --------------------------------------------------
    # 5. Update review status
    # --------------------------------------------------
    match.match_status = request.match_status

    # --------------------------------------------------
    # 6. Calculate confidence information
    # --------------------------------------------------
    confidence = build_confidence_result(
        match.final_confidence_score
    )

    # --------------------------------------------------
    # 7. Update explanation
    # --------------------------------------------------
    explanation = match.explanation or "{}"

    try:
        explanation_data = json.loads(explanation)
        explanation_data["confidence"] = {
            "score": confidence["confidence_score"],
            "level": confidence["confidence_level"]
        }
        explanation_data["human_review"] = {
            "reviewed_by": current_user.id,
            "review_status": request.match_status,
            "review_notes": request.review_notes
        }
        match.explanation = json.dumps(
            explanation_data,
            default=str
        )
    except Exception:
        pass

    # --------------------------------------------------
    # 8. Synchronize HarmonizedFeature
    # --------------------------------------------------
    hf = (
        db.query(HarmonizedFeature)
        .filter(
            HarmonizedFeature.project_id == match.project_id,
            HarmonizedFeature.match_id == match.id
        )
        .first()
    )

    if hf:
        hf.review_status = request.match_status
        if request.review_notes:
            try:
                attrs = json.loads(hf.harmonized_attributes) if hf.harmonized_attributes else {}
                attrs["review_notes"] = request.review_notes
                hf.harmonized_attributes = json.dumps(attrs, default=str)
            except Exception:
                pass
    else:
        # Create HarmonizedFeature from target spatial feature
        target_sf = db.query(SpatialFeature).filter(SpatialFeature.id == match.target_feature_id).first()
        source_sf = db.query(SpatialFeature).filter(SpatialFeature.id == match.source_feature_id).first()
        if target_sf:
            try:
                target_props = json.loads(target_sf.properties) if target_sf.properties else {}
            except Exception:
                target_props = {}
            if source_sf:
                try:
                    source_props = json.loads(source_sf.properties) if source_sf.properties else {}
                    for k, v in source_props.items():
                        if k not in target_props:
                            target_props[k] = v
                except Exception:
                    pass

            new_hf = HarmonizedFeature(
                project_id=match.project_id,
                feature_id=target_sf.id,
                match_id=match.id,
                feature_type=target_sf.feature_type or "land_parcel",
                geometry=target_sf.geometry,
                harmonized_attributes=json.dumps(target_props, default=str),
                confidence_score=match.final_confidence_score,
                review_status=request.match_status
            )
            db.add(new_hf)

    # --------------------------------------------------
    # 9. Create Audit Log
    # --------------------------------------------------
    create_audit_log(
        db=db,
        user_id=current_user.id,
        project_id=match.project_id,
        action="match_reviewed",
        entity_type="feature_match",
        entity_id=match.id,
        description=(
            f"Feature match #{match.id} (Source #{match.source_feature_id} <-> Target #{match.target_feature_id}) "
            f"reviewed as '{request.match_status}'. Confidence: {round((match.final_confidence_score or 0) * 100)}%"
        )
    )

    # --------------------------------------------------
    # 10. Save changes
    # --------------------------------------------------
    db.commit()
    db.refresh(match)

    # --------------------------------------------------
    # 11. Return review result
    # --------------------------------------------------
    return {
        "message": "Feature match review updated successfully",
        "match_id": match.id,
        "project_id": match.project_id,
        "source_feature_id": match.source_feature_id,
        "target_feature_id": match.target_feature_id,
        "confidence_score": confidence["confidence_score"],
        "confidence_level": confidence["confidence_level"],
        "match_status": match.match_status,
        "reviewed_by": current_user.id,
        "review_notes": request.review_notes
    }