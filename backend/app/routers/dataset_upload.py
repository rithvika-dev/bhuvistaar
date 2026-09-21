import os
import re

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.file_validation import (
    validate_file_extension,
    get_file_type
)
from app.config import settings

router = APIRouter(
    prefix="/datasets",
    tags=["Dataset Upload"]
)

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB limit


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.-]", "_", clean)
    return clean


@router.post("/{dataset_id}/upload")
async def upload_dataset_file(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Find project
    project = db.query(Project).filter(Project.id == dataset.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check project ownership
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this dataset")

    # Validate file presence
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Validate extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Allowed formats: "
                "GeoJSON, JSON, SHP, GPKG, KML, KMZ, "
                "GeoTIFF, CSV and ZIP"
            )
        )

    file_type = get_file_type(file.filename)
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    safe_filename = sanitize_filename(file.filename)
    target_path = os.path.abspath(os.path.join(upload_dir, f"{dataset_id}_{safe_filename}"))

    # Path traversal protection
    if not target_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="Invalid target file path attempt.")

    # Save uploaded file with 500MB size check
    total_bytes = 0
    with open(target_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                buffer.close()
                if os.path.exists(target_path):
                    os.remove(target_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of 500 MB (received > {total_bytes / (1024*1024):.1f} MB)."
                )
            buffer.write(chunk)

    # Update dataset record
    dataset.file_name = safe_filename
    dataset.file_path = target_path
    dataset.status = "uploaded"

    # Audit log
    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        project_id=dataset.project_id,
        action="dataset_uploaded",
        entity_type="dataset",
        entity_id=dataset.id,
        description=f"File '{safe_filename}' ({total_bytes / (1024*1024):.2f} MB, {file_type}) uploaded."
    )

    db.commit()
    db.refresh(dataset)

    return {
        "message": "Dataset file uploaded successfully",
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "file_type": file_type,
        "file_path": dataset.file_path,
        "file_size_mb": round(total_bytes / (1024 * 1024), 2),
        "status": dataset.status
    }