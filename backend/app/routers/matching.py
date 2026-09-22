from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.matching_service import run_feature_matching


router = APIRouter(
    prefix="/matching",
    tags=["Feature Matching"]
)


@router.post("/run")
def run_matching(
    project_id: int,
    source_dataset_id: Optional[int] = None,
    target_dataset_id: Optional[int] = None,
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

    # Source and target must be different (if both provided)
    if (
        source_dataset_id is not None
        and target_dataset_id is not None
        and source_dataset_id == target_dataset_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Source and target datasets must be different"
        )

    try:
        result = run_feature_matching(
            db=db,
            project_id=project_id,
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id
        )

        return result

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError as error:
        db.rollback()

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Feature matching failed: {str(error)}"
        )