from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.change_detection import ChangeDetection
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/change-detection",
    tags=["Change Detection Review"]
)


class ChangeDetectionReviewRequest(BaseModel):
    review_status: str
    review_notes: str | None = None


@router.put("/{change_id}/review")
def review_change(
    change_id: int,
    request: ChangeDetectionReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    change = (
        db.query(ChangeDetection)
        .filter(
            ChangeDetection.id == change_id
        )
        .first()
    )

    if not change:
        raise HTTPException(
            status_code=404,
            detail="Change detection record not found"
        )

    project = (
        db.query(Project)
        .filter(
            Project.id == change.project_id
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
            detail="You do not have access to this change record"
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

    change.review_status = request.review_status

    if request.review_notes:
        existing_description = change.description or ""

        change.description = (
            existing_description
            + f"\nReview Notes: {request.review_notes}"
        )

    db.commit()
    db.refresh(change)

    return {
        "message": (
            "Change detection review "
            "updated successfully"
        ),
        "change_id": change.id,
        "project_id": change.project_id,
        "change_type": change.change_type,
        "change_score": change.change_score,
        "review_status": change.review_status,
        "review_notes": request.review_notes
    }