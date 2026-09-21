import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.gis.raster_inspector import inspect_raster_file
from app.gis.raster_processor import reproject_raster, extract_raster_features
from app.config import settings

router = APIRouter(
    prefix="/raster",
    tags=["Raster"]
)


def verify_dataset_access(db: Session, dataset_id: int, user_id: int) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    project = db.query(Project).filter(Project.id == dataset.project_id).first()
    if not project or project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return dataset


@router.post("/{dataset_id}/inspect")
def inspect_raster(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full raster metadata inspection including band statistics, CRS, resolution."""
    dataset = verify_dataset_access(db, dataset_id, current_user.id)

    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="No file uploaded for this dataset")

    try:
        result = inspect_raster_file(dataset.file_path)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Raster inspection failed: {str(e)}")


class RasterProcessRequest(BaseModel):
    target_crs: str = "EPSG:4326"


@router.post("/{dataset_id}/process")
def process_raster(
    dataset_id: int,
    request: RasterProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reproject raster to target CRS. Output saved to processed/ directory."""
    dataset = verify_dataset_access(db, dataset_id, current_user.id)

    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="No file uploaded for this dataset")

    processed_dir = settings.PROCESSED_DIR
    os.makedirs(processed_dir, exist_ok=True)

    basename = os.path.basename(dataset.file_path)
    output_path = os.path.join(processed_dir, f"reprojected_{dataset_id}_{basename}")

    try:
        result = reproject_raster(dataset.file_path, output_path, request.target_crs)

        # Audit
        from app.services.audit_service import create_audit_log
        create_audit_log(
            db=db,
            user_id=current_user.id,
            project_id=dataset.project_id,
            action="raster_processed",
            entity_type="dataset",
            entity_id=dataset_id,
            description=f"Raster reprojected to {request.target_crs}"
        )

        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Raster processing failed: {str(e)}")


class FeatureExtractionRequest(BaseModel):
    band_index: int = 1
    canny_low: int = 50
    canny_high: int = 150


@router.post("/{dataset_id}/extract-features")
def extract_features(
    dataset_id: int,
    request: FeatureExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract candidate boundary features from a raster using OpenCV edge detection.
    PROTOTYPE: Results require human review before any official use.
    """
    dataset = verify_dataset_access(db, dataset_id, current_user.id)

    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="No file uploaded for this dataset")

    try:
        result = extract_raster_features(
            file_path=dataset.file_path,
            band_index=request.band_index,
            canny_low=request.canny_low,
            canny_high=request.canny_high
        )

        from app.services.audit_service import create_audit_log
        create_audit_log(
            db=db,
            user_id=current_user.id,
            project_id=dataset.project_id,
            action="raster_features_extracted",
            entity_type="dataset",
            entity_id=dataset_id,
            description=(
                f"Extracted {result['candidate_feature_count']} candidate features "
                f"from band {request.band_index}"
            )
        )

        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {str(e)}")
