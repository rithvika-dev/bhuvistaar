from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.project import Project
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.pipeline_service import start_pipeline

router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline"]
)


class PipelineStartRequest(BaseModel):
    project_id: int
    source_dataset_id: int
    target_dataset_id: int


@router.post("/start")
def start_end_to_end_pipeline(
    request: PipelineStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start the complete end-to-end BhuVistaar geospatial data harmonization pipeline.
    """
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to run pipeline for this project")

    try:
        return start_pipeline(
            db=db,
            project_id=request.project_id,
            source_dataset_id=request.source_dataset_id,
            target_dataset_id=request.target_dataset_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/{project_id}/status")
def get_pipeline_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest pipeline progress & status for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    latest_job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.project_id == project_id,
            ProcessingJob.job_type == "end_to_end_pipeline"
        )
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )

    if not latest_job:
        return {"status": "not_started", "message": "No pipeline jobs executed for this project yet."}

    return {
        "job_id": latest_job.id,
        "project_id": project_id,
        "status": latest_job.status,
        "progress": latest_job.progress,
        "message": latest_job.message,
        "error_message": latest_job.error_message,
        "created_at": str(latest_job.created_at),
        "completed_at": str(latest_job.completed_at) if latest_job.completed_at else None
    }
