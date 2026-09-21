from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.validation_result import ValidationResult
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/validation-results",
    tags=["Validation Results"]
)


@router.get("/{project_id}")
def get_validation_results(
    project_id: int,
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

    validations = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.project_id == project_id
        )
        .order_by(
            ValidationResult.created_at.desc()
        )
        .all()
    )

    results = []

    for validation in validations:

        results.append(
            {
                "id": validation.id,
                "feature_id": validation.feature_id,
                "validation_type": (
                    validation.validation_type
                ),
                "status": validation.status,
                "severity": validation.severity,
                "message": validation.message,
                "confidence_score": (
                    validation.confidence_score
                ),
                "created_at": validation.created_at
            }
        )

    return {
        "project_id": project_id,
        "validation_count": len(results),
        "validations": results
    }