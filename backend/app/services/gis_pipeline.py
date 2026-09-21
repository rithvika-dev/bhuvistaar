import os

import geopandas as gpd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset

from app.services.version_service import create_dataset_version
from app.gis.crs import normalize_crs
from app.gis.feature_extractor import extract_features
from app.services.feature_storage import store_features


def process_vector_dataset(
    db: Session,
    dataset: Dataset
) -> dict:
    """
    Process a vector dataset through the initial GIS pipeline.

    Pipeline:
    1. Validate file
    2. Create dataset version
    3. Read vector data
    4. Check CRS
    5. Normalize CRS
    6. Extract features
    7. Store features in PostGIS
    """

    # --------------------------------------------------
    # 1. Validate dataset file
    # --------------------------------------------------

    if not dataset.file_path:
        raise ValueError("Dataset does not have an uploaded file")

    if not os.path.exists(dataset.file_path):
        raise FileNotFoundError(
            f"Dataset file not found: {dataset.file_path}"
        )

    # --------------------------------------------------
    # 2. Create dataset version
    # --------------------------------------------------

    version = create_dataset_version(
        db=db,
        dataset=dataset
    )

    # --------------------------------------------------
    # 3. Read vector dataset
    # --------------------------------------------------

    gdf = gpd.read_file(dataset.file_path)

    if gdf.empty:
        raise ValueError("Dataset contains no features")

    # --------------------------------------------------
    # 4. Check CRS
    # --------------------------------------------------

    if gdf.crs is None:

        version.processing_status = "georeferencing_required"
        version.processing_notes = (
            "Dataset has no CRS. "
            "Georeferencing is required before processing."
        )

        db.commit()

        return {
            "status": "georeferencing_required",
            "dataset_id": dataset.id,
            "version_id": version.id,
            "message": (
                "Dataset does not contain CRS information."
            )
        }

    # --------------------------------------------------
    # 5. Normalize CRS
    # --------------------------------------------------

    normalized_gdf = normalize_crs(gdf)

    # Update version CRS
    version.crs = str(normalized_gdf.crs)

    # --------------------------------------------------
    # 6. Extract features
    # --------------------------------------------------

    features = extract_features(
        normalized_gdf
    )

    if not features:
        raise ValueError(
            "No valid spatial features were found"
        )

    # --------------------------------------------------
    # 7. Store features in PostGIS
    # --------------------------------------------------

    stored_count = store_features(
        db=db,
        dataset_version_id=version.id,
        features=features
    )

    # --------------------------------------------------
    # 8. Update processing status
    # --------------------------------------------------

    version.processing_status = "completed"

    version.processing_notes = (
        f"Processed {stored_count} spatial features "
        f"and normalized CRS to EPSG:4326."
    )

    dataset.crs = str(normalized_gdf.crs)
    dataset.status = "processed"

    db.commit()

    return {
        "status": "completed",
        "dataset_id": dataset.id,
        "version_id": version.id,
        "original_feature_count": len(gdf),
        "stored_feature_count": stored_count,
        "original_crs": str(gdf.crs),
        "normalized_crs": str(normalized_gdf.crs)
    }