from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def create_audit_log(
    db: Session,
    user_id: Optional[int],
    project_id: Optional[int],
    action: str,
    entity_type: Optional[str],
    entity_id: Optional[int],
    description: Optional[str] = None
) -> AuditLog:
    """
    Creates an audit log entry in the database.
    """
    audit_log = AuditLog(
        user_id=user_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log
