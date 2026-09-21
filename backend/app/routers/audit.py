from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user

router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)

@router.get("/{project_id}")
def get_audit_logs(
    project_id: int,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    # Query audit logs
    query = db.query(AuditLog).filter(AuditLog.project_id == project_id)

    if action:
        query = query.filter(AuditLog.action == action)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    # Return in chronological order as requested
    logs = query.order_by(AuditLog.created_at.asc()).offset(skip).limit(limit).all()

    return {
        "status": "completed",
        "project_id": project_id,
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": logs
    }
