from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.migrations.add_indexes import run_migrations

# Models
from app.models.user import User
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.spatial_feature import SpatialFeature
from app.models.attribute_mapping import AttributeMapping
from app.models.conflict import Conflict
from app.models.harmonized_feature import HarmonizedFeature
from app.models.validation_result import ValidationResult
from app.models.change_detection import ChangeDetection
from app.models.processing_job import ProcessingJob
from app.models.audit_log import AuditLog
from app.models.feature_match import FeatureMatch
from app.models.ground_control_point import GroundControlPoint
from app.models.export_record import ExportRecord

# Routers
from app.routers.auth import router as auth_router
from app.routers.project import router as project_router
from app.routers.dataset import router as dataset_router
from app.routers.dataset_upload import router as dataset_upload_router
from app.routers.gis_processing import router as gis_processing_router
from app.routers.features import router as features_router
from app.routers.matching import router as matching_router
from app.routers.match_results import router as match_results_router
from app.routers.conflicts import router as conflicts_router
from app.routers.conflict_results import router as conflict_results_router
from app.routers.conflict_resolution import router as conflict_resolution_router
from app.routers.topology import router as topology_router
from app.routers.validation_results import router as validation_results_router
from app.routers.harmonization import router as harmonization_router
from app.routers.mapping_resolution import router as mapping_resolution_router
from app.routers.harmonized_features import (
    router as harmonized_features_router
)
from app.routers.harmonized_feature_review import (
    router as harmonized_feature_review_router
)
from app.routers.change_detection import (
    router as change_detection_router
)
from app.routers.change_detection_review import (
    router as change_detection_review_router
)
from app.routers.ml_training import router as ml_training_router
from app.routers.review_training import router as review_training_router
from app.routers.ml_retraining import router as ml_retraining_router
from app.routers.match_review import router as match_review_router
from app.routers.pending_matches import router as pending_matches_router
from app.routers.dataset_status import router as dataset_status_router
from app.routers.ml_status import router as ml_status_router
from app.routers.audit import router as audit_router
from app.routers.jobs import router as jobs_router
from app.routers.georeferencing import router as georeferencing_router
from app.routers.raster import router as raster_router
from app.routers.exports import router as exports_router
from app.routers.pipeline import router as pipeline_router

# Ensure schema matches the current model set and backfill any legacy/missing columns.
run_migrations()
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="BhuVistaar API",
    description="AI-powered multi-source geospatial data integration and harmonization system",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "BhuVistaar API is running"
    }


# Health endpoints
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "BhuVistaar"
    }


@app.get("/health/database", tags=["System"])
def health_database():
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "healthy", "postgis": "healthy"}
    except Exception as e:
        return {"database": "unhealthy", "error": str(e)}


@app.get("/health/redis", tags=["System"])
def health_redis():
    try:
        import redis
        from app.config import settings
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        return {"redis": "healthy"}
    except Exception as e:
        return {"redis": "unavailable", "message": "Redis server not responding", "error": str(e)}


@app.get("/health/celery", tags=["System"])
def health_celery():
    try:
        from app.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=2)
        ping_result = inspector.ping()
        if ping_result:
            return {"celery": "healthy", "workers": ping_result}
        return {"celery": "degraded", "message": "No active Celery workers responded to ping."}
    except Exception as e:
        return {"celery": "unavailable", "error": str(e)}


@app.get("/system/status", tags=["System"])
def system_status():
    db_st = health_database()
    redis_st = health_redis()
    celery_st = health_celery()
    return {
        "system": "BhuVistaar SIH 2026 Platform",
        "version": "1.0.0",
        "database": db_st.get("database"),
        "postgis": db_st.get("postgis"),
        "redis": redis_st.get("redis"),
        "celery": celery_st.get("celery"),
        "ml_model": "ready"
    }


# Register routers
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(dataset_router)
app.include_router(dataset_upload_router)
app.include_router(gis_processing_router)
app.include_router(features_router)
app.include_router(matching_router)
app.include_router(match_results_router)
app.include_router(conflicts_router)
app.include_router(conflict_results_router)
app.include_router(conflict_resolution_router)
app.include_router(topology_router)
app.include_router(validation_results_router)
app.include_router(harmonization_router)
app.include_router(mapping_resolution_router)
app.include_router(harmonized_features_router)
app.include_router(harmonized_feature_review_router)
app.include_router(change_detection_router)
app.include_router(change_detection_review_router)
app.include_router(ml_training_router)
app.include_router(review_training_router)
app.include_router(ml_retraining_router)
app.include_router(match_review_router)
app.include_router(pending_matches_router)
app.include_router(ml_status_router)
app.include_router(dataset_status_router)
app.include_router(audit_router)
app.include_router(jobs_router)
app.include_router(georeferencing_router)
app.include_router(raster_router)
app.include_router(exports_router)
app.include_router(pipeline_router)