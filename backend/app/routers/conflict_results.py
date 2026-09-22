from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conflict import Conflict
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/conflict-results",
    tags=["Conflict Results"]
)


@router.get("/{project_id}")
def get_conflict_results(
    project_id: int,
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    severity: Optional[str] = Query(None, description="Filter by severity (high, medium, low)"),
    status: Optional[str] = Query(None, description="Filter by resolution status"),
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

    query = (
        db.query(Conflict)
        .filter(Conflict.project_id == project_id)
    )

    if conflict_type and conflict_type != "all":
        query = query.filter(Conflict.conflict_type == conflict_type)

    if severity and severity != "all":
        query = query.filter(Conflict.severity == severity.lower())

    if status and status != "all":
        query = query.filter(Conflict.resolution_status == status.lower())

    conflicts = query.order_by(Conflict.id.asc()).all()

    results = []
    for conflict in conflicts:
        results.append(
            {
                "id": conflict.id,
                "project_id": conflict.project_id,
                "feature_id": conflict.feature_id,
                "conflict_type": conflict.conflict_type,
                "severity": conflict.severity or "medium",
                "description": conflict.description,
                "source_value": conflict.source_value,
                "target_value": conflict.target_value,
                "confidence_score": conflict.confidence_score,
                "suggested_resolution": conflict.suggested_resolution,
                "resolution_status": conflict.resolution_status,
                "resolution_notes": conflict.resolution_notes,
                "created_at": conflict.created_at
            }
        )

    return {
        "project_id": project_id,
        "conflict_count": len(results),
        "conflicts": results
    }