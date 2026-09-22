from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func


from app.database import Base


class Conflict(Base):
    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    feature_id = Column(
        Integer,
        ForeignKey("spatial_features.id"),
        nullable=True
    )

    conflict_type = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    source_value = Column(
        Text,
        nullable=True
    )

    target_value = Column(
        Text,
        nullable=True
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    severity = Column(
        String(50),
        nullable=True,
        default="medium"
    )

    suggested_resolution = Column(
        Text,
        nullable=True
    )

    resolution_status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    resolution_notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )