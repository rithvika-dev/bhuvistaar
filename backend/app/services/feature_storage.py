import json

from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape

from app.models.spatial_feature import SpatialFeature


def store_features(
    db: Session,
    dataset_version_id: int,
    features: list
) -> int:
    """
    Store extracted GIS features in PostGIS.
    """

    stored_count = 0

    for feature in features:

        geometry = feature.get("geometry")

        if geometry is None:
            continue

        spatial_feature = SpatialFeature(
            dataset_version_id=dataset_version_id,
            feature_type=feature["feature_type"],
            feature_code=str(feature["source_index"]),
            geometry=from_shape(
                geometry,
                srid=4326
            ),
            properties=json.dumps(
                feature.get("attributes", {}),
                default=str
            ),
            confidence_score=None
        )

        db.add(spatial_feature)
        stored_count += 1

    db.commit()

    return stored_count