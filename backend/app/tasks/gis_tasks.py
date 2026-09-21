import datetime
import traceback
from typing import Optional
from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.processing_job import ProcessingJob
from app.models.dataset import Dataset
from app.services.gis_pipeline import process_vector_dataset

logger = get_task_logger(__name__)

def update_job_status(
    db: Session, 
    job_id: int, 
    status: str, 
    progress: float, 
    message: Optional[str] = None, 
    error_message: Optional[str] = None
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        return
    
    job.status = status
    job.progress = progress
    if message:
        job.message = message
    if error_message:
        job.error_message = error_message
        
    if status in ["completed", "failed", "cancelled"]:
        job.completed_at = datetime.datetime.utcnow()
        
    db.commit()


@celery_app.task(bind=True, name="tasks.process_dataset")
def task_process_dataset(self, job_id: int, dataset_id: int):
    logger.info(f"Starting dataset processing task for job {job_id}")
    db = SessionLocal()
    try:
        update_job_status(db, job_id, "running", 0.0, "Starting dataset processing")
        
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        # Run the actual synchronous processing logic
        result = process_vector_dataset(db=db, dataset=dataset)
        
        update_job_status(
            db, 
            job_id, 
            "completed", 
            100.0, 
            f"Processing complete: {result.get('message', '')}"
        )
        return result
    except Exception as e:
        logger.error(f"Error in task_process_dataset: {str(e)}\n{traceback.format_exc()}")
        update_job_status(db, job_id, "failed", 0.0, "Processing failed", str(e))
        raise
    finally:
        db.close()

# Placeholders for future tasks
@celery_app.task(bind=True, name="tasks.run_matching")
def task_run_matching(self, job_id: int, project_id: int, source_dataset_id: int, target_dataset_id: int):
    pass

@celery_app.task(bind=True, name="tasks.validate_topology")
def task_validate_topology(self, job_id: int, project_id: int, dataset_id: int):
    pass

@celery_app.task(bind=True, name="tasks.detect_conflicts")
def task_detect_conflicts(self, job_id: int, project_id: int, source_dataset_id: int, target_dataset_id: int):
    pass

@celery_app.task(bind=True, name="tasks.run_harmonization")
def task_run_harmonization(self, job_id: int, project_id: int, mapping_rules: dict):
    pass

@celery_app.task(bind=True, name="tasks.detect_changes")
def task_detect_changes(self, job_id: int, project_id: int, old_version_id: int, new_version_id: int):
    pass

@celery_app.task(bind=True, name="tasks.train_model")
def task_train_model(self, job_id: int, project_id: int):
    pass

@celery_app.task(bind=True, name="tasks.georeference")
def task_georeference(self, job_id: int, dataset_id: int):
    pass

@celery_app.task(bind=True, name="tasks.raster_processing")
def task_raster_processing(self, job_id: int, dataset_id: int):
    pass

@celery_app.task(bind=True, name="tasks.export")
def task_export(self, job_id: int, export_id: int):
    pass
