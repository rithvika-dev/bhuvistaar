import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.harmonized_feature import HarmonizedFeature
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.harmonized_feature_service import (
    generate_harmonized_features
)

router = APIRouter(
    prefix="/harmonized-features",
    tags=["Harmonized Features"]
)


@router.get("/{project_id}")
def get_project_harmonized_features(
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

    features = (
        db.query(HarmonizedFeature)
        .filter(HarmonizedFeature.project_id == project_id)
        .order_by(HarmonizedFeature.id.desc())
        .all()
    )

    serialized = []
    for feature in features:
        properties = {}
        if feature.harmonized_attributes:
            try:
                properties = json.loads(feature.harmonized_attributes)
            except (TypeError, ValueError):
                properties = {"raw": feature.harmonized_attributes}

        source_info = None
        if getattr(feature, "source_info", None):
            try:
                source_info = json.loads(feature.source_info)
            except (TypeError, ValueError):
                source_info = {"raw": feature.source_info}

        serialized.append({
            "id": feature.id,
            "project_id": feature.project_id,
            "feature_id": feature.feature_id,
            "match_id": getattr(feature, "match_id", None),
            "feature_type": feature.feature_type,
            "properties": properties,
            "confidence_score": feature.confidence_score,
            "review_status": feature.review_status,
            "source_info": source_info,
        })

    return {
        "project_id": project_id,
        "count": len(serialized),
        "features": serialized,
    }


@router.post("/generate/{project_id}")
def generate_features(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check project
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

    # Check ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    try:
        result = generate_harmonized_features(
            db=db,
            project_id=project_id
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Harmonization failed: {str(e)}"
        )