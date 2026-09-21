from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExportCreateRequest(BaseModel):
    project_id: int
    export_type: str = Field(
        ...,
        description="One of: harmonized_features, validation_results, conflicts, change_detection, audit_logs"
    )
    format: str = Field(
        "geojson",
        description="Format: geojson, csv, geopackage (gpkg)"
    )


class ExportResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    export_type: str
    format: str
    file_name: str
    file_path: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
