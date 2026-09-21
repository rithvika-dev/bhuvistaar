from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.topology_service import validate_dataset_topology


router = APIRouter(
    prefix="/topology",
    tags=["Topology Validation"]
)


@router.post("/validate")
def validate_topology(
    project_id: int,
    dataset_id: int,
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

    try:
        result = validate_dataset_topology(
            db=db,
            project_id=project_id,
            dataset_id=dataset_id
        )

        return result

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except FileNotFoundError as error:
        db.rollback()

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Topology validation failed: {str(error)}"
        )