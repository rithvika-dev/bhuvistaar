from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.routers.features import get_dataset_features as get_dataset_features_route
from app.services.auth_dependency import get_current_user
from app.services.gis_pipeline import process_vector_dataset


router = APIRouter(
    prefix="/gis",
    tags=["GIS Processing"]
)


@router.get("/datasets/{dataset_id}/features")
def get_dataset_features_compat(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compatibility endpoint for GIS clients expecting features under /gis."""
    return get_dataset_features_route(
        dataset_id=dataset_id,
        db=db,
        current_user=current_user
    )


@router.post("/datasets/{dataset_id}/process")
def process_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process an uploaded vector dataset.
    """

    # Find dataset
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

    # Find project
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

    # Check ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this dataset"
        )

    # Check uploaded file
    if not dataset.file_path:
        raise HTTPException(
            status_code=400,
            detail="No file has been uploaded for this dataset"
        )

    try:
        result = process_vector_dataset(
            db=db,
            dataset=dataset
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"GIS processing failed: {str(error)}"
        )