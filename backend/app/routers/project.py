from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.post(
    "/",
    response_model=ProjectResponse
)
def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_project = Project(
        name=request.name,
        description=request.description,
        location=request.location,
        owner_id=current_user.id,
        status="created"
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        project_id=new_project.id,
        action="project_created",
        entity_type="project",
        entity_id=new_project.id,
        description=f"Project '{new_project.name}' created"
    )

    return new_project