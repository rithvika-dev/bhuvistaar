from sqlalchemy.orm import Session
from app.models.ground_control_point import GroundControlPoint
from app.models.dataset import Dataset
from app.models.spatial_feature import SpatialFeature
from app.schemas.georeferencing import GCPCreate
from app.gis.georeferencing import validate_gcps, transform_with_gcps, calculate_residuals, calculate_transform_matrix
import geopandas as gpd
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import shape
import json

def create_gcp(db: Session, dataset_id: int, gcp_in: GCPCreate):
    gcp = GroundControlPoint(
        dataset_id=dataset_id,
        source_x=gcp_in.source_x,
        source_y=gcp_in.source_y,
        target_x=gcp_in.target_x,
        target_y=gcp_in.target_y,
        target_crs=gcp_in.target_crs,
        label=gcp_in.label
    )
    db.add(gcp)
    db.commit()
    db.refresh(gcp)
    return gcp

def list_gcps(db: Session, dataset_id: int):
    return db.query(GroundControlPoint).filter(GroundControlPoint.dataset_id == dataset_id).all()

def validate_dataset_gcps(db: Session, dataset_id: int):
    gcps = list_gcps(db, dataset_id)
    validation = validate_gcps(gcps)
    if validation["is_valid"]:
        try:
            matrix = calculate_transform_matrix(gcps, method="affine")
            rmse, _ = calculate_residuals(gcps, matrix)
            validation["estimated_rmse"] = rmse
        except Exception as e:
            validation["is_valid"] = False
            validation["errors"].append(str(e))
    return validation

def execute_georeferencing(db: Session, dataset_id: int, method: str = "affine"):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise ValueError("Dataset not found")
        
    gcps = list_gcps(db, dataset_id)
    validation = validate_gcps(gcps)
    if not validation["is_valid"]:
        raise ValueError(f"Invalid GCPs: {', '.join(validation['errors'])}")
        
    # Get spatial features as a GeoDataFrame
    features = db.query(SpatialFeature).filter(SpatialFeature.dataset_id == dataset_id).all()
    if not features:
        raise ValueError("No spatial features found for dataset")
        
    geometries = []
    properties = []
    
    for f in features:
        geom = to_shape(f.geometry)
        geometries.append(geom)
        properties.append(f.properties)
        
    gdf = gpd.GeoDataFrame(properties, geometry=geometries)
    
    transformed_gdf, matrix = transform_with_gcps(gdf, gcps, method=method)
    rmse, residuals = calculate_residuals(gcps, matrix)
    
    # Update geometries in database
    target_crs = gcps[0].target_crs
    for i, f in enumerate(features):
        f.geometry = from_shape(transformed_gdf.geometry.iloc[i], srid=int(target_crs.split(":")[1]))
        
    # Record georeferencing status
    dataset.status = "georeferenced"
    
    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=None,
        project_id=dataset.project_id,
        action="dataset_georeferenced",
        entity_type="dataset",
        entity_id=dataset_id,
        description=f"Georeferenced dataset using {method} with RMSE {rmse:.4f}"
    )
    
    db.commit()
    
    return {
        "dataset_id": dataset_id,
        "status": "success",
        "method": method,
        "rmse": rmse,
        "points_used": len(gcps),
        "transformation_matrix": matrix.flatten().tolist() if matrix is not None else None,
        "message": "Georeferencing applied successfully"
    }

def get_georeferencing_result(db: Session, dataset_id: int):
    # Retrieve current stats
    gcps = list_gcps(db, dataset_id)
    if not gcps:
        return {"status": "no_gcps"}
    
    try:
        matrix = calculate_transform_matrix(gcps, method="affine")
        rmse, residuals = calculate_residuals(gcps, matrix)
        return {
            "dataset_id": dataset_id,
            "status": "ready",
            "method": "affine",
            "rmse": rmse,
            "points_used": len(gcps),
            "transformation_matrix": matrix.flatten().tolist(),
            "message": "GCPs valid and ready to apply"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
