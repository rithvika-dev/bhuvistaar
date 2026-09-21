from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class GroundControlPoint(Base):
    __tablename__ = "ground_control_points"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    source_x = Column(Float, nullable=False)
    source_y = Column(Float, nullable=False)
    target_x = Column(Float, nullable=False)
    target_y = Column(Float, nullable=False)
    target_crs = Column(String(50), nullable=False)
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
