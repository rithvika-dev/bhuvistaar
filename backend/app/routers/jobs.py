from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.processing_job import ProcessingJob
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.user import User
from app.services.auth_dependency import get_current_user

# Import celery tasks
from app.tasks.gis_tasks import task_process_dataset

router = APIRouter(
    prefix="/jobs",
    tags=["Background Jobs"]
)

@router.post("/submit/{job_type}")
def submit_job(
    job_type: str,
    project_id: int,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create job record
    job = ProcessingJob(
        project_id=project_id,
        dataset_id=dataset_id,
        job_type=job_type,
        status="queued",
        progress=0.0,
        message="Job queued for processing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to celery if Redis is available, else fallback logic could be here
    try:
        if job_type == "process_dataset" and dataset_id:
            task_process_dataset.delay(job.id, dataset_id)
        # Add other dispatches as they are fully implemented
    except Exception as e:
        # If celery is down, update status to reflect it
        job.status = "failed"
        job.error_message = f"Failed to dispatch to task queue: {str(e)}"
        db.commit()
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    return {"message": f"Job {job_type} submitted", "job_id": job.id}

@router.get("/{job_id}")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    project = db.query(Project).filter(Project.id == job.project_id).first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "dataset_id": job.dataset_id,
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

@router.get("/project/{project_id}")
def list_project_jobs(
    project_id: int,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = db.query(ProcessingJob).filter(ProcessingJob.project_id == project_id)
    
    if job_type:
        query = query.filter(ProcessingJob.job_type == job_type)
    if status:
        query = query.filter(ProcessingJob.status == status)
        
    jobs = query.order_by(ProcessingJob.created_at.desc()).all()
    return jobs
