from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.harmonization_service import (
    suggest_attribute_mappings
)


router = APIRouter(
    prefix="/harmonization",
    tags=["Attribute Harmonization"]
)


class AttributeMappingRequest(BaseModel):
    project_id: int
    source_dataset_id: int
    target_dataset_id: int
    source_fields: list[str]
    target_fields: list[str]


@router.post("/suggest-mappings")
def suggest_mappings(
    request: AttributeMappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = (
        db.query(Project)
        .filter(
            Project.id == request.project_id
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
            detail="You do not have access to this project"
        )

    if (
        request.source_dataset_id
        == request.target_dataset_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Source and target datasets "
                "must be different"
            )
        )

    if not request.source_fields:
        raise HTTPException(
            status_code=400,
            detail="Source fields cannot be empty"
        )

    if not request.target_fields:
        raise HTTPException(
            status_code=400,
            detail="Target fields cannot be empty"
        )

    try:

        result = suggest_attribute_mappings(
            db=db,
            project_id=request.project_id,
            source_dataset_id=(
                request.source_dataset_id
            ),
            target_dataset_id=(
                request.target_dataset_id
            ),
            source_fields=request.source_fields,
            target_fields=request.target_fields
        )

        return result

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Attribute harmonization failed: "
                f"{str(error)}"
            )
        )