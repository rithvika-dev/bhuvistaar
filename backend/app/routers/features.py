import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.dataset_version import DatasetVersion
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/features",
    tags=["Spatial Features"]
)


@router.get("/dataset/{dataset_id}")
def get_dataset_features(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all spatial features belonging to a dataset.
    """

    # Find dataset
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    # Find project
    project = (
        db.query(Project)
        .filter(Project.id == dataset.project_id)
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
            detail="You do not have access to this dataset"
        )

    # Get latest dataset version
    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )

    if not version:
        return {
            "dataset_id": dataset_id,
            "feature_count": 0,
            "features": []
        }

    # Retrieve features and convert geometry to GeoJSON
    query = text("""
        SELECT
            id,
            feature_type,
            feature_code,
            properties,
            ST_AsGeoJSON(geometry) AS geometry,
            confidence_score
        FROM spatial_features
        WHERE dataset_version_id = :version_id
        ORDER BY id
    """)

    rows = db.execute(
        query,
        {"version_id": version.id}
    ).fetchall()

    features = []

    for row in rows:
        geometry = row.geometry
        if isinstance(geometry, str):
            try:
                geometry = json.loads(geometry)
            except (TypeError, ValueError):
                geometry = None

        properties = row.properties or {}
        if isinstance(properties, str):
            try:
                properties = json.loads(properties)
            except (TypeError, ValueError):
                properties = {}

        features.append({
            "type": "Feature",
            "id": row.id,
            "properties": {
                **(properties if isinstance(properties, dict) else {}),
                "feature_type": row.feature_type,
                "feature_code": row.feature_code,
                "confidence_score": row.confidence_score,
            },
            "geometry": geometry,
        })

    return {
        "type": "FeatureCollection",
        "dataset_id": dataset_id,
        "version_id": version.id,
        "feature_count": len(features),
        "features": features
    }