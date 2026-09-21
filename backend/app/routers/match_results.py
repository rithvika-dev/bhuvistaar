from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feature_match import FeatureMatch
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/match-results",
    tags=["Match Results"]
)


@router.get("/{project_id}")
def get_match_results(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check project
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

    # Check ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    # Get matching results
    matches = (
        db.query(FeatureMatch)
        .filter(
            FeatureMatch.project_id == project_id
        )
        .order_by(
            FeatureMatch.final_confidence_score.desc()
        )
        .all()
    )

    results = []

    for match in matches:
        results.append(
            {
                "id": match.id,
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
                "final_confidence_score":
                    match.final_confidence_score,
                "match_status":
                    match.match_status,
                "explanation":
                    match.explanation,
                "created_at":
                    match.created_at
            }
        )

    return {
        "project_id": project_id,
        "match_count": len(results),
        "matches": results
    }