from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.change_detection_service import (
    detect_changes_between_features,
    detect_changes_between_versions
)

router = APIRouter(
    prefix="/change-detection",
    tags=["Change Detection"]
)


class FeatureChangeDetectionRequest(BaseModel):
    project_id: int
    old_feature_id: int
    new_feature_id: int


class VersionChangeDetectionRequest(BaseModel):
    project_id: int
    old_version_id: int
    new_version_id: int


@router.post("/detect")
def detect_change(
    request: FeatureChangeDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect changes between a specific feature pair."""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    try:
        return detect_changes_between_features(
            db=db,
            project_id=request.project_id,
            old_feature_id=request.old_feature_id,
            new_feature_id=request.new_feature_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change detection failed: {str(e)}")


@router.post("/detect-versions")
def detect_version_changes(
    request: VersionChangeDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Automatically detect all changes (added, removed, modified, unchanged) between dataset versions."""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    try:
        return detect_changes_between_versions(
            db=db,
            project_id=request.project_id,
            old_version_id=request.old_version_id,
            new_version_id=request.new_version_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Version change detection failed: {str(e)}")