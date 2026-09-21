from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class AttributeMapping(Base):
    __tablename__ = "attribute_mappings"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    source_dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False
    )

    target_dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False
    )

    source_field = Column(
        String(150),
        nullable=False
    )

    target_field = Column(
        String(150),
        nullable=False
    )

    mapping_type = Column(
        String(100),
        nullable=True
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    mapping_status = Column(
        String(50),
        nullable=False,
        default="suggested"
    )

    notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )