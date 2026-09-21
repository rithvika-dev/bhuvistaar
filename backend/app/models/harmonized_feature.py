from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.database import Base


class HarmonizedFeature(Base):
    __tablename__ = "harmonized_features"

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

    match_id = Column(
        Integer,
        ForeignKey("feature_matches.id"),
        nullable=True
    )

    feature_type = Column(
        String(100),
        nullable=False
    )

    geometry = Column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326
        ),
        nullable=True
    )

    harmonized_attributes = Column(
        Text,
        nullable=True
    )

    source_info = Column(
        Text,
        nullable=True,
        comment="JSON storing complete provenance: source dataset, target dataset, source feature, target feature, match ID, attribute mappings, conflicts, validation status"
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    review_status = Column(
        String(50),
        nullable=False,
        default="pending"  # pending, approved, rejected
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )