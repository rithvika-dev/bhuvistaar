from pydantic import BaseModel
from typing import Optional


class DatasetCreate(BaseModel):
    project_id: int
    name: str
    dataset_type: str
    source: Optional[str] = None
    crs: Optional[str] = None
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    project_id: int
    name: str
    dataset_type: str
    file_name: Optional[str]
    file_path: Optional[str]
    source: Optional[str]
    crs: Optional[str]
    status: str
    description: Optional[str]

    class Config:
        from_attributes = True