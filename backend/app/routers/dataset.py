from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.schemas.dataset import DatasetCreate, DatasetResponse
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


@router.get(
    "/project/{project_id}",
    response_model=list[DatasetResponse]
)
def list_project_datasets(
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

    return (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


@router.post(
    "/",
    response_model=DatasetResponse
)
def create_dataset(
    request: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check whether the project exists
    project = db.query(Project).filter(
        Project.id == request.project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Check whether the logged-in user owns the project
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    # Create dataset
    new_dataset = Dataset(
        project_id=request.project_id,
        name=request.name,
        dataset_type=request.dataset_type,
        source=request.source,
        crs=request.crs,
        description=request.description,
        status="uploaded"
    )

    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    return new_dataset