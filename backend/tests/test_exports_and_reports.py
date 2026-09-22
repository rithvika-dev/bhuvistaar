import os
import zipfile
import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project import Project
from app.models.user import User
from app.models.harmonized_feature import HarmonizedFeature
from app.services.export_service import create_export
from app.services.report_service import generate_project_summary_report


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_test_project_and_user(db: Session):
    project = db.query(Project).join(HarmonizedFeature, HarmonizedFeature.project_id == Project.id).first()
    if not project:
        project = db.query(Project).filter(Project.id.in_([4, 19])).first()
    if not project:
        project = db.query(Project).first()

    user = db.query(User).filter(User.id == project.owner_id).first() if project else None
    if not user:
        user = db.query(User).first()
    return project, user


def test_export_geopackage(db: Session):
    project, user = get_test_project_and_user(db)
    assert project is not None, "At least one project must exist in the database"

    rec = create_export(
        db=db,
        project_id=project.id,
        user_id=user.id,
        export_type="harmonized_features",
        export_format="geopackage"
    )

    assert rec is not None
    assert rec.format == "geopackage"
    assert rec.file_path.endswith(".gpkg")
    assert os.path.exists(rec.file_path)
    assert os.path.getsize(rec.file_path) > 0


def test_export_title_ledger(db: Session):
    project, user = get_test_project_and_user(db)
    assert project is not None

    rec = create_export(
        db=db,
        project_id=project.id,
        user_id=user.id,
        export_type="title_ledger",
        export_format="csv"
    )

    assert rec is not None
    assert rec.format == "csv"
    assert rec.file_path.endswith(".csv")
    assert os.path.exists(rec.file_path)
    assert os.path.getsize(rec.file_path) > 0


def test_export_master_dossier_zip(db: Session):
    project, user = get_test_project_and_user(db)
    assert project is not None

    rec = create_export(
        db=db,
        project_id=project.id,
        user_id=user.id,
        export_type="master_dossier",
        export_format="zip"
    )

    assert rec is not None
    assert rec.format == "zip"
    assert rec.file_path.endswith(".zip")
    assert os.path.exists(rec.file_path)
    assert os.path.getsize(rec.file_path) > 0

    # Verify zip content
    with zipfile.ZipFile(rec.file_path, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) > 0
        assert any("Summary" in name or "README" in name for name in namelist)


def test_generate_project_summary_report(db: Session):
    project, _ = get_test_project_and_user(db)
    assert project is not None

    report = generate_project_summary_report(db, project.id)
    assert report["status"] == "completed"
    assert report["project_id"] == project.id
    assert "datasets" in report
    assert "matched_features" in report
    assert "conflicts" in report
    assert "change_detections" in report
    assert "reports" in report
    assert len(report["reports"]) == 5
