from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    name = Column(
        String(150),
        nullable=False
    )

    dataset_type = Column(
        String(100),
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=True
    )

    file_path = Column(
        String(500),
        nullable=True
    )

    source = Column(
        String(150),
        nullable=True
    )

    crs = Column(
        String(100),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="uploaded"
    )

    description = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )