from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False
    )

    version_number = Column(
        Integer,
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=True
    )

    crs = Column(
        String(100),
        nullable=True
    )

    processing_status = Column(
        String(50),
        nullable=False,
        default="created"
    )

    processing_notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )