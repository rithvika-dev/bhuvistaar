import os

import joblib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/ml",
    tags=["AI / ML"]
)


MODEL_PATH = "processed/ml_models/feature_match_model.pkl"


@router.get("/status")
def get_ml_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # --------------------------------------------------
    # 1. Check project
    # --------------------------------------------------
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

    # --------------------------------------------------
    # 2. Check ownership
    # --------------------------------------------------
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this project"
        )

    # --------------------------------------------------
    # 3. Check model file
    # --------------------------------------------------
    model_exists = os.path.exists(
        MODEL_PATH
    )

    model_loadable = False

    if model_exists:

        try:
            joblib.load(MODEL_PATH)
            model_loadable = True

        except Exception:
            model_loadable = False

    # --------------------------------------------------
    # 4. Determine status
    # --------------------------------------------------
    if model_loadable:
        status = "ready"
    elif model_exists:
        status = "model_file_invalid"
    else:
        status = "not_trained"

    # --------------------------------------------------
    # 5. Return status
    # --------------------------------------------------
    return {
        "status": status,
        "project_id": project_id,
        "model_exists": model_exists,
        "model_loadable": model_loadable,
        "model_type": "RandomForestClassifier",
        "model_path": MODEL_PATH
    }