from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.conflict import Conflict
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.conflict_service import resolve_conflict as service_resolve_conflict


router = APIRouter(
    prefix="/conflicts",
    tags=["Conflict Resolution"]
)


class ConflictResolutionRequest(BaseModel):
    resolution_status: str
    resolution_notes: str | None = None


@router.put("/{conflict_id}/resolve")
def resolve_conflict_endpoint(
    conflict_id: int,
    request: ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conflict = (
        db.query(Conflict)
        .filter(Conflict.id == conflict_id)
        .first()
    )

    if not conflict:
        raise HTTPException(
            status_code=404,
            detail="Conflict not found"
        )

    project = (
        db.query(Project)
        .filter(Project.id == conflict.project_id)
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
            detail="You do not have access to this conflict"
        )

    try:
        result = service_resolve_conflict(
            db=db,
            conflict_id=conflict_id,
            resolution_status=request.resolution_status,
            resolution_notes=request.resolution_notes,
            user_id=current_user.id
        )
        return {
            "message": "Conflict resolution updated successfully",
            "conflict_id": result["conflict_id"],
            "resolution_status": result["resolution_status"],
            "resolution_notes": result["resolution_notes"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conflict resolution failed: {str(e)}")