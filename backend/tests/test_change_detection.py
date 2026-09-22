import pytest
from app.database import SessionLocal
from app.services.change_detection_service import detect_changes_between_versions, get_project_change_detections
from app.models.change_detection import ChangeDetection


def test_detect_changes_between_versions_project_4():
    db = SessionLocal()
    try:
        # First execution
        result = detect_changes_between_versions(db, 4)
        assert result["status"] == "completed"
        assert result["total_changes"] == len(result["changes"])
        assert result["total_changes"] > 0

        summary = result["changes_summary"]
        expected_total = (
            summary["added"]
            + summary["removed"]
            + summary["geometry_modified"]
            + summary["attributes_modified"]
            + summary["both_modified"]
        )
        assert result["total_changes"] == expected_total

        # Check land-use conversion for P005 (Agricultural -> Residential)
        p005_changes = [c for c in result["changes"] if c["parcelId"] == "P005"]
        assert len(p005_changes) == 1
        assert p005_changes[0]["category"] == "land_use"

        # Check newly added building B011
        added_changes = [c for c in result["changes"] if c["change_type"] == "added"]
        assert len(added_changes) == summary["added"]

        # Check database rows
        rows_1 = db.query(ChangeDetection).filter(ChangeDetection.project_id == 4).count()
        assert rows_1 == len(result["changes"])

        # Second execution to test idempotent deduplication
        result_2 = detect_changes_between_versions(db, 4)
        rows_2 = db.query(ChangeDetection).filter(ChangeDetection.project_id == 4).count()
        assert rows_2 == rows_1, "Repeated execution must not create duplicate records in change_detections."

    finally:
        db.close()


def test_get_project_change_detections_service():
    db = SessionLocal()
    try:
        result = get_project_change_detections(db, 4)
        assert result["status"] == "completed"
        assert len(result["changes"]) > 0
    finally:
        db.close()
