from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.conflict import Conflict
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/conflicts",
    tags=["Conflict Resolution"]
)


class ConflictResolutionRequest(BaseModel):
    resolution_status: str
    resolution_notes: str | None = None


@router.put("/{conflict_id}/resolve")
def resolve_conflict(
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

    allowed_statuses = {
        "approved",
        "rejected",
        "resolved"
    }

    if request.resolution_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid resolution status. "
                "Use approved, rejected, or resolved."
            )
        )

    conflict.resolution_status = request.resolution_status
    conflict.resolution_notes = request.resolution_notes

    db.commit()
    db.refresh(conflict)

    return {
        "message": "Conflict resolution updated successfully",
        "conflict_id": conflict.id,
        "resolution_status": conflict.resolution_status,
        "resolution_notes": conflict.resolution_notes
    }