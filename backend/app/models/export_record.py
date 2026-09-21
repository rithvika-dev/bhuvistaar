from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ExportRecord(Base):
    __tablename__ = "export_records"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    export_type = Column(
        String(100),
        nullable=False  # harmonized_features, validation_results, conflicts, change_detection, audit_logs
    )

    format = Column(
        String(50),
        nullable=False  # geojson, csv, geopackage
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="completed"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
