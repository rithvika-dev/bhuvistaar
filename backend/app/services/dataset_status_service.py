from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion


def update_dataset_status(
    db: Session,
    dataset_id: int,
    status: str
) -> Dataset:

    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )

    if not dataset:
        raise ValueError(
            "Dataset not found"
        )

    dataset.status = status

    db.commit()
    db.refresh(dataset)

    return dataset


def get_dataset_processing_status(
    db: Session,
    dataset_id: int
) -> dict:

    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )

    if not dataset:
        raise ValueError(
            "Dataset not found"
        )

    latest_version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.dataset_id
            == dataset_id
        )
        .order_by(
            DatasetVersion.version_number.desc()
        )
        .first()
    )

    return {
        "dataset_id":
            dataset.id,

        "dataset_name":
            dataset.name,

        "dataset_status":
            dataset.status,

        "latest_version":
            latest_version.version_number
            if latest_version
            else None,

        "processing_status":
            latest_version.processing_status
            if latest_version
            else None,

        "processing_notes":
            latest_version.processing_notes
            if latest_version
            else None,

        "crs":
            dataset.crs,

        "file_name":
            dataset.file_name
    }