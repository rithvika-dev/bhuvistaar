from sqlalchemy.orm import Session

from app.models.dataset_version import DatasetVersion
from app.models.dataset import Dataset


def create_dataset_version(
    db: Session,
    dataset: Dataset
) -> DatasetVersion:
    """
    Create the next version for a dataset.
    """

    latest_version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset.id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )

    if latest_version:
        next_version = latest_version.version_number + 1
    else:
        next_version = 1

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=next_version,
        file_path=dataset.file_path,
        crs=dataset.crs,
        processing_status="created",
        processing_notes=None
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return version