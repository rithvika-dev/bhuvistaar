from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.dataset_status_service import (
    get_dataset_processing_status
)


router = APIRouter(
    prefix="/datasets",
    tags=["Dataset Status"]
)


@router.get("/{dataset_id}/status")
def get_dataset_status(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Find dataset
    # --------------------------------------------------
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    # --------------------------------------------------
    # 2. Find project
    # --------------------------------------------------
    project = (
        db.query(Project)
        .filter(Project.id == dataset.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # --------------------------------------------------
    # 3. Check ownership
    # --------------------------------------------------
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this dataset"
        )

    # --------------------------------------------------
    # 4. Get processing status
    # --------------------------------------------------
    try:

        result = get_dataset_processing_status(
            db=db,
            dataset_id=dataset_id
        )

        return {
            "status": "completed",
            **result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to get dataset status: "
                f"{str(error)}"
            )
        )