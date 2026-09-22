from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.conflict_service import detect_conflicts


router = APIRouter(
    prefix="/conflicts",
    tags=["Conflict Detection"]
)


@router.post("/detect/{project_id}")
def run_conflict_detection(
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

    try:
        result = detect_conflicts(
            db=db,
            project_id=project_id,
            user_id=current_user.id
        )

        return result

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Conflict detection failed: {str(error)}"
        )