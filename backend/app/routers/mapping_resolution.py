from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.attribute_mapping import AttributeMapping
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/attribute-mappings",
    tags=["Attribute Mapping Resolution"]
)


@router.get("/project/{project_id}")
def get_project_attribute_mappings(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    mappings = db.query(AttributeMapping).filter(AttributeMapping.project_id == project_id).all()
    return {
        "project_id": project_id,
        "count": len(mappings),
        "mappings": [
            {
                "id": m.id,
                "project_id": m.project_id,
                "source_dataset_id": m.source_dataset_id,
                "target_dataset_id": m.target_dataset_id,
                "source_field": m.source_field,
                "target_field": m.target_field,
                "mapping_type": m.mapping_type,
                "confidence_score": m.confidence_score,
                "mapping_status": m.mapping_status,
                "notes": m.notes,
            }
            for m in mappings
        ]
    }


class MappingResolutionRequest(BaseModel):
    mapping_status: str
    notes: str | None = None


@router.put("/{mapping_id}/resolve")
def resolve_mapping(
    mapping_id: int,
    request: MappingResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    mapping = (
        db.query(AttributeMapping)
        .filter(
            AttributeMapping.id == mapping_id
        )
        .first()
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Attribute mapping not found"
        )

    project = (
        db.query(Project)
        .filter(
            Project.id == mapping.project_id
        )
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
            detail=(
                "You do not have access "
                "to this mapping"
            )
        )

    allowed_statuses = {
        "approved",
        "rejected"
    }

    if request.mapping_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid mapping status. "
                "Use approved or rejected."
            )
        )

    mapping.mapping_status = (
        request.mapping_status
    )

    if request.notes:
        mapping.notes = request.notes

    db.commit()
    db.refresh(mapping)

    return {
        "message": (
            "Attribute mapping resolution "
            "updated successfully"
        ),
        "mapping_id": mapping.id,
        "source_field": mapping.source_field,
        "target_field": mapping.target_field,
        "mapping_status": mapping.mapping_status,
        "confidence_score": (
            mapping.confidence_score
        ),
        "notes": mapping.notes
    }