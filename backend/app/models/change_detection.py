from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func


from app.database import Base


class ChangeDetection(Base):
    __tablename__ = "change_detections"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    old_feature_id = Column(
        Integer,
        ForeignKey("spatial_features.id"),
        nullable=True
    )

    new_feature_id = Column(
        Integer,
        ForeignKey("spatial_features.id"),
        nullable=True
    )

    change_type = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    change_score = Column(
        Float,
        nullable=True
    )

    review_status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )