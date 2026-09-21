from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feature_match import FeatureMatch
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.ai.confidence_service import build_confidence_result


router = APIRouter(
    prefix="/match-results",
    tags=["Feature Match Review"]
)


@router.get("/pending/{project_id}")
def get_pending_matches(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Check project
    # --------------------------------------------------
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # --------------------------------------------------
    # 2. Check project ownership
    # --------------------------------------------------
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    # --------------------------------------------------
    # 3. Get pending matches
    # --------------------------------------------------
    matches = (
        db.query(FeatureMatch)
        .filter(
            FeatureMatch.project_id == project_id,
            FeatureMatch.match_status == "suggested"
        )
        .order_by(
            FeatureMatch.final_confidence_score.desc()
        )
        .all()
    )

    # --------------------------------------------------
    # 4. Prepare response
    # --------------------------------------------------
    match_results = []

    for match in matches:

        confidence = build_confidence_result(
            match.final_confidence_score
        )

        match_results.append(
            {
                "match_id": match.id,

                "source_feature_id":
                    match.source_feature_id,

                "target_feature_id":
                    match.target_feature_id,

                "spatial_score":
                    match.spatial_score,

                "attribute_score":
                    match.attribute_score,

                "geometry_similarity":
                    match.geometry_similarity,

                "proximity_score":
                    match.proximity_score,

                "distance":
                    match.distance,

                "confidence_score":
                    confidence["confidence_score"],

                "confidence_level":
                    confidence["confidence_level"],

                "match_status":
                    match.match_status,

                "explanation":
                    match.explanation
            }
        )

    # --------------------------------------------------
    # 5. Return pending matches
    # --------------------------------------------------
    return {
        "status": "completed",

        "project_id":
            project_id,

        "pending_count":
            len(match_results),

        "matches":
            match_results
    }