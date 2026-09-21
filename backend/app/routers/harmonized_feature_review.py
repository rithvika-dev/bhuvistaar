from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.harmonized_feature import HarmonizedFeature
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/harmonized-features",
    tags=["Harmonized Feature Review"]
)


class HarmonizedFeatureReviewRequest(BaseModel):
    review_status: str
    review_notes: str | None = None


@router.put("/{feature_id}/review")
def review_harmonized_feature(
    feature_id: int,
    request: HarmonizedFeatureReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    feature = (
        db.query(HarmonizedFeature)
        .filter(
            HarmonizedFeature.id == feature_id
        )
        .first()
    )

    if not feature:
        raise HTTPException(
            status_code=404,
            detail="Harmonized feature not found"
        )

    project = (
        db.query(Project)
        .filter(
            Project.id == feature.project_id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this feature"
        )

    allowed_statuses = {
        "approved",
        "rejected"
    }

    if request.review_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid review status. "
                "Use approved or rejected."
            )
        )

    feature.review_status = request.review_status

    if request.review_notes:
        current_attributes = feature.harmonized_attributes or ""

        feature.harmonized_attributes = (
            current_attributes
            + f'\nReview Notes: {request.review_notes}'
        )

    db.commit()
    db.refresh(feature)

    return {
        "message": (
            "Harmonized feature review "
            "updated successfully"
        ),
        "feature_id": feature.id,
        "project_id": feature.project_id,
        "review_status": feature.review_status,
        "confidence_score": feature.confidence_score,
        "review_notes": request.review_notes
    }