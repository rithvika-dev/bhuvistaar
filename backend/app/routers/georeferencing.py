from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.schemas.georeferencing import (
    GCPCreate, GCPResponse, GCPValidationResult, 
    GeoreferenceExecute, GeoreferenceResult
)
from app.services.georeferencing_service import (
    create_gcp, list_gcps, validate_dataset_gcps, 
    execute_georeferencing, get_georeferencing_result
)

router = APIRouter(
    prefix="/georeferencing",
    tags=["Georeferencing"]
)

def verify_dataset_access(db: Session, dataset_id: int, user_id: int):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    project = db.query(Project).filter(Project.id == dataset.project_id).first()
    if not project or project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return dataset

@router.post("/{dataset_id}/gcps", response_model=GCPResponse)
def add_gcp(
    dataset_id: int,
    gcp: GCPCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_dataset_access(db, dataset_id, current_user.id)
    return create_gcp(db, dataset_id, gcp)

@router.get("/{dataset_id}/gcps", response_model=List[GCPResponse])
def get_gcps(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_dataset_access(db, dataset_id, current_user.id)
    return list_gcps(db, dataset_id)

@router.post("/{dataset_id}/validate", response_model=GCPValidationResult)
def validate_gcps_endpoint(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_dataset_access(db, dataset_id, current_user.id)
    return validate_dataset_gcps(db, dataset_id)

@router.post("/{dataset_id}/execute", response_model=GeoreferenceResult)
def execute_georeferencing_endpoint(
    dataset_id: int,
    request: GeoreferenceExecute,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_dataset_access(db, dataset_id, current_user.id)
    try:
        return execute_georeferencing(db, dataset_id, method=request.method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}/result")
def get_result(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_dataset_access(db, dataset_id, current_user.id)
    return get_georeferencing_result(db, dataset_id)
