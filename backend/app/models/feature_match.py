from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class FeatureMatch(Base):
    __tablename__ = "feature_matches"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    source_feature_id = Column(
        Integer,
        ForeignKey("spatial_features.id"),
        nullable=False
    )

    target_feature_id = Column(
        Integer,
        ForeignKey("spatial_features.id"),
        nullable=False
    )

    spatial_score = Column(
        Float,
        nullable=True
    )

    attribute_score = Column(
        Float,
        nullable=True
    )

    geometry_similarity = Column(
        Float,
        nullable=True
    )

    proximity_score = Column(
        Float,
        nullable=True
    )

    distance = Column(
        Float,
        nullable=True
    )

    final_confidence_score = Column(
        Float,
        nullable=True
    )

    match_status = Column(
        String(50),
        nullable=False,
        default="suggested"
    )

    explanation = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )