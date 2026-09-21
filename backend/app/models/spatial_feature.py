from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.database import Base


class SpatialFeature(Base):
    __tablename__ = "spatial_features"

    id = Column(Integer, primary_key=True, index=True)

    dataset_version_id = Column(
        Integer,
        ForeignKey("dataset_versions.id"),
        nullable=False,
        index=True
    )

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=True,
        index=True
    )

    feature_type = Column(
        String(100),
        nullable=False
    )

    feature_code = Column(
        String(100),
        nullable=True,
        index=True
    )

    geometry = Column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326
        ),
        nullable=True
    )

    properties = Column(
        Text,
        nullable=True
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )