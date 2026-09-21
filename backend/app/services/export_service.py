"""
Export Service for BhuVistaar geospatial & analytical data.

Exports:
  - harmonized_features -> GeoJSON, CSV, GeoPackage (gpkg)
  - validation_results  -> CSV
  - conflicts           -> CSV
  - change_detection    -> CSV
  - audit_logs          -> CSV

Safe file paths, isolated in exports/ directory, prevents path traversal.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import geopandas as gpd
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.config import settings
from app.models.export_record import ExportRecord
from app.models.harmonized_feature import HarmonizedFeature
from app.models.validation_result import ValidationResult
from app.models.conflict import Conflict
from app.models.change_detection import ChangeDetection
from app.models.audit_log import AuditLog
from app.services.audit_service import create_audit_log


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.-]", "_", clean)
    return clean


def create_export(
    db: Session,
    project_id: int,
    user_id: int,
    export_type: str,
    export_format: str
) -> ExportRecord:

    export_dir = settings.EXPORT_DIR
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    export_type_clean = sanitize_filename(export_type.lower())
    format_clean = export_format.lower().strip()
    if format_clean == "gpkg":
        format_clean = "geopackage"

    ext = "json" if format_clean == "geojson" else ("gpkg" if format_clean == "geopackage" else "csv")
    file_name = f"{export_type_clean}_p{project_id}_{timestamp}.{ext}"
    file_path = os.path.abspath(os.path.join(export_dir, file_name))

    # Path traversal safety check
    if not file_path.startswith(os.path.abspath(export_dir)):
        raise ValueError("Invalid export file path attempt.")

    # 1. Harmonized features export
    if export_type_clean == "harmonized_features":
        features = db.query(HarmonizedFeature).filter(HarmonizedFeature.project_id == project_id).all()
        if not features:
            raise ValueError("No harmonized features found for this project to export.")

        rows = []
        geoms = []
        for f in features:
            props = json.loads(f.harmonized_attributes) if f.harmonized_attributes else {}
            props["harmonized_feature_id"] = f.id
            props["feature_type"] = f.feature_type
            props["confidence_score"] = f.confidence_score
            props["review_status"] = f.review_status
            rows.append(props)
            geoms.append(to_shape(f.geometry) if f.geometry else None)

        gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:4326")

        if format_clean == "geojson":
            gdf.to_file(file_path, driver="GeoJSON")
        elif format_clean == "geopackage":
            gdf.to_file(file_path, driver="GPKG")
        elif format_clean == "csv":
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False)
        else:
            raise ValueError(f"Unsupported format '{export_format}' for harmonized_features export.")

    # 2. Validation results export
    elif export_type_clean == "validation_results":
        results = db.query(ValidationResult).filter(ValidationResult.project_id == project_id).all()
        rows = [
            {
                "id": r.id,
                "validation_type": r.validation_type,
                "status": r.status,
                "severity": r.severity,
                "message": r.message,
                "confidence_score": r.confidence_score,
                "created_at": str(r.created_at)
            }
            for r in results
        ]
        pd.DataFrame(rows).to_csv(file_path, index=False)

    # 3. Conflicts export
    elif export_type_clean == "conflicts":
        conflicts = db.query(Conflict).filter(Conflict.project_id == project_id).all()
        rows = [
            {
                "id": c.id,
                "conflict_type": c.conflict_type,
                "description": c.description,
                "source_value": c.source_value,
                "target_value": c.target_value,
                "confidence_score": c.confidence_score,
                "resolution_status": c.resolution_status,
                "resolution_notes": c.resolution_notes,
                "created_at": str(c.created_at)
            }
            for c in conflicts
        ]
        pd.DataFrame(rows).to_csv(file_path, index=False)

    # 4. Change detection export
    elif export_type_clean == "change_detection":
        changes = db.query(ChangeDetection).filter(ChangeDetection.project_id == project_id).all()
        rows = [
            {
                "id": c.id,
                "old_feature_id": c.old_feature_id,
                "new_feature_id": c.new_feature_id,
                "change_type": c.change_type,
                "description": c.description,
                "change_score": c.change_score,
                "review_status": c.review_status,
                "created_at": str(c.created_at)
            }
            for c in changes
        ]
        pd.DataFrame(rows).to_csv(file_path, index=False)

    # 5. Audit logs export
    elif export_type_clean == "audit_logs":
        logs = db.query(AuditLog).filter(AuditLog.project_id == project_id).all()
        rows = [
            {
                "id": a.id,
                "user_id": a.user_id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "description": a.description,
                "created_at": str(a.created_at)
            }
            for a in logs
        ]
        pd.DataFrame(rows).to_csv(file_path, index=False)

    else:
        raise ValueError(f"Unsupported export_type '{export_type}'. Supported: harmonized_features, validation_results, conflicts, change_detection, audit_logs.")

    export_rec = ExportRecord(
        project_id=project_id,
        user_id=user_id,
        export_type=export_type_clean,
        format=format_clean,
        file_path=file_path,
        file_name=file_name,
        status="completed"
    )
    db.add(export_rec)
    db.commit()
    db.refresh(export_rec)

    # Audit log
    create_audit_log(
        db=db,
        user_id=user_id,
        project_id=project_id,
        action="export_created",
        entity_type="export",
        entity_id=export_rec.id,
        description=f"Export '{file_name}' ({export_type}, {export_format}) generated."
    )

    return export_rec
