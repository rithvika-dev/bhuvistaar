from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.ai.retrain_model import retrain_from_reviews


router = APIRouter(
    prefix="/ml",
    tags=["AI / ML"]
)


@router.post("/retrain")
def retrain_model(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ----------------------------------------------
    # Check project
    # ----------------------------------------------
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

    # ----------------------------------------------
    # Check ownership
    # ----------------------------------------------
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    # ----------------------------------------------
    # Retrain model
    # ----------------------------------------------
    try:
        result = retrain_from_reviews(
            db=db,
            project_id=project_id
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ML retraining failed: {str(e)}"
        )