import json
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.audit_service import create_audit_log

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

DEFAULT_SETTINGS = {
    "crs_default": "EPSG:4326",
    "active_zone": "EPSG:32643",
    "iou_threshold": 85,
    "buffer_distance": 2.5,
    "fuzzy_threshold": 80,
    "storage_engine": "IndexedDB / Browser Local DB",
    "hashing_algorithm": "SHA-256",
    "organization": "Ministry of Rural Development",
    "department": "Department of Land Resources (DoLR)",
    "node_identifier": "NODE-SIH26013-W17 (Urban Pilot)"
}


class SettingsUpdateRequest(BaseModel):
    crs_default: Optional[str] = None
    active_zone: Optional[str] = None
    iou_threshold: Optional[float] = None
    buffer_distance: Optional[float] = None
    fuzzy_threshold: Optional[float] = None
    storage_engine: Optional[str] = None
    hashing_algorithm: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    node_identifier: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


@router.get("")
@router.get("/")
def get_settings(
    project_id: int = Query(..., description="Project ID to load settings for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access settings for this project")

    settings_data = dict(DEFAULT_SETTINGS)
    if project.settings:
        try:
            stored = json.loads(project.settings)
            if isinstance(stored, dict):
                settings_data.update(stored)
        except Exception:
            pass

    return {
        "status": "success",
        "project_id": project_id,
        "project_name": project.name,
        "settings": settings_data
    }


@router.put("")
@router.put("/")
def update_settings(
    request: SettingsUpdateRequest,
    project_id: int = Query(..., description="Project ID to update settings for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update settings for this project")

    # Load existing settings
    current_settings = dict(DEFAULT_SETTINGS)
    if project.settings:
        try:
            stored = json.loads(project.settings)
            if isinstance(stored, dict):
                current_settings.update(stored)
        except Exception:
            pass

    # Update with new non-null values
    update_dict = request.model_dump(exclude_unset=True, exclude_none=True)
    if "extra_config" in update_dict:
        extra = update_dict.pop("extra_config")
        if isinstance(extra, dict):
            update_dict.update(extra)

    current_settings.update(update_dict)

    # Persist to database
    project.settings = json.dumps(current_settings, default=str)
    db.commit()
    db.refresh(project)

    # Audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        action="settings_updated",
        entity_type="project_settings",
        entity_id=project.id,
        description=f"Settings updated for project {project.id} ({project.name}): CRS={current_settings.get('crs_default')}, IoU={current_settings.get('iou_threshold')}%"
    )

    return {
        "status": "success",
        "message": "Project settings saved successfully",
        "project_id": project_id,
        "settings": current_settings
    }
