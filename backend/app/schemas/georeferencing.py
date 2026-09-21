from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class GCPBase(BaseModel):
    source_x: float
    source_y: float
    target_x: float
    target_y: float
    target_crs: str
    label: Optional[str] = None

class GCPCreate(GCPBase):
    pass

class GCPResponse(GCPBase):
    id: int
    dataset_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GCPValidationResult(BaseModel):
    is_valid: bool
    point_count: int
    minimum_required: int
    has_duplicates: bool
    is_collinear: bool
    estimated_rmse: Optional[float] = None
    errors: List[str] = []

class GeoreferenceExecute(BaseModel):
    method: str = "affine" # affine or similarity

class GeoreferenceResult(BaseModel):
    dataset_id: int
    status: str
    method: str
    rmse: float
    points_used: int
    transformation_matrix: Optional[List[float]] = None
    message: str
