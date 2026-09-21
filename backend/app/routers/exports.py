import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.export_record import ExportRecord
from app.models.project import Project
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.schemas.export import ExportCreateRequest, ExportResponse
from app.services.export_service import create_export
from app.config import settings

router = APIRouter(
    prefix="/exports",
    tags=["Exports"]
)


@router.post("", response_model=ExportResponse)
@router.post("/", response_model=ExportResponse)
def generate_export(
    request: ExportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to export data from this project")

    try:
        export_rec = create_export(
            db=db,
            project_id=request.project_id,
            user_id=current_user.id,
            export_type=request.export_type,
            export_format=request.format
        )
        return export_rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


@router.get("/{export_id}", response_model=ExportResponse)
def get_export_info(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    export_rec = db.query(ExportRecord).filter(ExportRecord.id == export_id).first()
    if not export_rec:
        raise HTTPException(status_code=404, detail="Export record not found")

    project = db.query(Project).filter(Project.id == export_rec.project_id).first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return export_rec


@router.get("/download/{export_id}")
def download_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    export_rec = db.query(ExportRecord).filter(ExportRecord.id == export_id).first()
    if not export_rec:
        raise HTTPException(status_code=404, detail="Export record not found")

    project = db.query(Project).filter(Project.id == export_rec.project_id).first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Path traversal check
    base_dir = os.path.abspath(settings.EXPORT_DIR)
    file_path = os.path.abspath(export_rec.file_path)

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access denied: Path outside export directory.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file does not exist on disk.")

    media_type = "application/geo+json" if export_rec.format == "geojson" else (
        "application/x-sqlite3" if export_rec.format in ("geopackage", "gpkg") else "text/csv"
    )

    return FileResponse(
        path=file_path,
        filename=export_rec.file_name,
        media_type=media_type
    )
