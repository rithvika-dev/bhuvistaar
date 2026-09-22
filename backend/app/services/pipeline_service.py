"""
End-to-End Orchestrated Pipeline Service.

Orchestrates the entire BhuVistaar data harmonization workflow:
  1. File & Dataset Validation
  2. GIS Vector / Raster Inspection
  3. Metric CRS Projection & Feature Extraction
  4. Intelligent Feature Matching (Spatial + Attribute + ML)
  5. Advanced Conflict Detection (Idempotent)
  6. Topology Validation
  7. Attribute Mapping & Harmonized Feature Generation
  8. Provenance & Harmonization Readiness Summary

Updates ProcessingJob progress at every step for complete status tracking.
"""

import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.processing_job import ProcessingJob
from app.services.gis_pipeline import process_vector_dataset
from app.services.matching_service import run_feature_matching
from app.services.conflict_service import detect_conflicts
from app.services.topology_service import validate_dataset_topology
from app.services.harmonized_feature_service import generate_harmonized_features
from app.services.audit_service import create_audit_log


def update_pipeline_job(db: Session, job: ProcessingJob, progress: float, message: str, status: str = "running"):
    job.progress = progress
    job.message = message
    job.status = status
    if status in ("completed", "failed"):
        job.completed_at = datetime.datetime.utcnow()
    db.commit()


def start_pipeline(
    db: Session,
    project_id: int,
    source_dataset_id: int,
    target_dataset_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:

    # 1. Create tracking job
    job = ProcessingJob(
        project_id=project_id,
        dataset_id=source_dataset_id,
        job_type="end_to_end_pipeline",
        status="running",
        progress=5.0,
        message="Initiating end-to-end BhuVistaar pipeline"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # 2. Inspect & process source dataset
        update_pipeline_job(db, job, 15.0, "Processing source dataset...")
        source_ds = db.query(Dataset).filter(Dataset.id == source_dataset_id, Dataset.project_id == project_id).first()
        if not source_ds or not source_ds.file_path:
            raise ValueError(f"Source dataset {source_dataset_id} invalid or missing uploaded file.")

        source_result = process_vector_dataset(db=db, dataset=source_ds)

        # 3. Inspect & process target dataset
        update_pipeline_job(db, job, 30.0, "Processing target dataset...")
        target_ds = db.query(Dataset).filter(Dataset.id == target_dataset_id, Dataset.project_id == project_id).first()
        if not target_ds or not target_ds.file_path:
            raise ValueError(f"Target dataset {target_dataset_id} invalid or missing uploaded file.")

        target_result = process_vector_dataset(db=db, dataset=target_ds)

        # 4. Run intelligent spatial & attribute matching (Metric CRS)
        update_pipeline_job(db, job, 50.0, "Running AI intelligent feature matching in projected metric CRS...")
        matching_result = run_feature_matching(
            db=db,
            project_id=project_id,
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id
        )

        # 5. Advanced conflict detection
        update_pipeline_job(db, job, 65.0, "Detecting attribute, identity, geometry & duplicate conflicts...")
        conflicts_result = detect_conflicts(db=db, project_id=project_id, user_id=user_id)

        # 6. Topology validation
        update_pipeline_job(db, job, 80.0, "Validating topology (gaps, overlaps, self-intersections)...")
        topology_result = validate_dataset_topology(db=db, project_id=project_id, dataset_id=source_dataset_id)

        # 7. Generate harmonized features
        update_pipeline_job(db, job, 90.0, "Generating unified harmonized features with provenance...")
        harmonized_result = generate_harmonized_features(db=db, project_id=project_id)

        # 8. Complete audit log
        create_audit_log(
            db=db,
            user_id=user_id,
            project_id=project_id,
            action="pipeline_executed",
            entity_type="project",
            entity_id=project_id,
            description=f"End-to-end pipeline completed for source {source_dataset_id} and target {target_dataset_id}."
        )

        update_pipeline_job(db, job, 100.0, "Pipeline completed successfully!", status="completed")

        return {
            "status": "completed",
            "job_id": job.id,
            "project_id": project_id,
            "source_dataset_id": source_dataset_id,
            "target_dataset_id": target_dataset_id,
            "summary": {
                "source_feature_count": source_result.get("feature_count", 0),
                "target_feature_count": target_result.get("feature_count", 0),
                "matches_found": matching_result.get("matches_found", 0),
                "conflicts_detected": conflicts_result.get("conflicts_found", 0),
                "topology_issues_detected": topology_result.get("validation_count", 0),
                "harmonized_features_generated": harmonized_result.get("created_count", 0)
            },
            "completed_at": str(job.completed_at)
        }

    except Exception as e:
        update_pipeline_job(db, job, job.progress, f"Pipeline failed: {str(e)}", status="failed")
        job.error_message = str(e)
        db.commit()
        raise
