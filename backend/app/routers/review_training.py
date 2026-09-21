from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.ai.review_training_data import get_review_training_summary


router = APIRouter(
    prefix="/ml",
    tags=["AI / ML"]
)


@router.get("/review-training-summary/{project_id}")
def review_training_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    try:
        return get_review_training_summary(
            db=db,
            project_id=project_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect review data: {str(e)}"
        )