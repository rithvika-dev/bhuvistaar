import json
import os

import geopandas as gpd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.spatial_feature import SpatialFeature
from app.models.feature_match import FeatureMatch

from app.ai.matching_engine import find_intelligent_matches
from app.gis.feature_extractor import extract_features


def run_feature_matching(
    db: Session,
    project_id: int,
    source_dataset_id: int,
    target_dataset_id: int
) -> dict:

    # --------------------------------------------------
    # 1. Get source dataset
    # --------------------------------------------------
    source_dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == source_dataset_id,
            Dataset.project_id == project_id
        )
        .first()
    )

    if not source_dataset:
        raise ValueError("Source dataset not found")

    # --------------------------------------------------
    # 2. Get target dataset
    # --------------------------------------------------
    target_dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == target_dataset_id,
            Dataset.project_id == project_id
        )
        .first()
    )

    if not target_dataset:
        raise ValueError("Target dataset not found")

    # --------------------------------------------------
    # 3. Check uploaded files
    # --------------------------------------------------
    if not source_dataset.file_path:
        raise ValueError(
            "Source dataset has no uploaded file"
        )

    if not target_dataset.file_path:
        raise ValueError(
            "Target dataset has no uploaded file"
        )

    if not os.path.exists(source_dataset.file_path):
        raise FileNotFoundError(
            "Source dataset file does not exist"
        )

    if not os.path.exists(target_dataset.file_path):
        raise FileNotFoundError(
            "Target dataset file does not exist"
        )

    # --------------------------------------------------
    # 4. Get latest processed versions
    # --------------------------------------------------
    source_version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.dataset_id == source_dataset_id
        )
        .order_by(
            DatasetVersion.version_number.desc()
        )
        .first()
    )

    target_version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.dataset_id == target_dataset_id
        )
        .order_by(
            DatasetVersion.version_number.desc()
        )
        .first()
    )

    if not source_version:
        raise ValueError(
            "Source dataset has not been processed yet"
        )

    if not target_version:
        raise ValueError(
            "Target dataset has not been processed yet"
        )

    # --------------------------------------------------
    # 5. Read both datasets
    # --------------------------------------------------
    source_gdf = gpd.read_file(
        source_dataset.file_path
    )

    target_gdf = gpd.read_file(
        target_dataset.file_path
    )

    if source_gdf.empty:
        raise ValueError(
            "Source dataset contains no features"
        )

    if target_gdf.empty:
        raise ValueError(
            "Target dataset contains no features"
        )

    # --------------------------------------------------
    # 6. Check CRS
    # --------------------------------------------------
    if source_gdf.crs is None:
        raise ValueError(
            "Source dataset CRS is missing"
        )

    if target_gdf.crs is None:
        raise ValueError(
            "Target dataset CRS is missing"
        )

    # --------------------------------------------------
    # 7. Normalize both to EPSG:4326 for storage/display
    #    (spatial_matcher will project internally to metric CRS)
    # --------------------------------------------------
    if source_gdf.crs.to_epsg() != 4326:
        source_gdf = source_gdf.to_crs("EPSG:4326")

    if target_gdf.crs.to_epsg() != 4326:
        target_gdf = target_gdf.to_crs("EPSG:4326")

    # --------------------------------------------------
    # 8. Extract features
    # --------------------------------------------------
    source_features = extract_features(source_gdf)
    target_features = extract_features(target_gdf)

    if not source_features:
        raise ValueError("No valid source features found")

    if not target_features:
        raise ValueError("No valid target features found")

    # --------------------------------------------------
    # 9. Run intelligent matching with METRIC threshold
    #    distance_threshold_meters=50 means 50 metres.
    #    spatial_matcher internally auto-selects UTM CRS.
    # --------------------------------------------------
    matches = find_intelligent_matches(
        source_gdf=source_gdf,
        target_gdf=target_gdf,
        source_features=source_features,
        target_features=target_features,
        distance_threshold_meters=50.0
    )

    # --------------------------------------------------
    # 10. Save matches
    # --------------------------------------------------
    saved_matches = []

    for match in matches:

        source_index = match[
            "source_index"
        ]

        target_index = match[
            "target_index"
        ]

        # ----------------------------------------------
        # Find source spatial feature
        # ----------------------------------------------
        source_spatial_feature = (
            db.query(SpatialFeature)
            .filter(
                SpatialFeature.dataset_version_id
                == source_version.id,

                SpatialFeature.feature_code
                == str(source_index)
            )
            .first()
        )

        # ----------------------------------------------
        # Find target spatial feature
        # ----------------------------------------------
        target_spatial_feature = (
            db.query(SpatialFeature)
            .filter(
                SpatialFeature.dataset_version_id
                == target_version.id,

                SpatialFeature.feature_code
                == str(target_index)
            )
            .first()
        )

        if not source_spatial_feature:
            continue

        if not target_spatial_feature:
            continue

        # ----------------------------------------------
        # Confidence information
        # ----------------------------------------------
        confidence_score = match[
            "final_confidence_score"
        ]

        confidence_level = match.get(
            "confidence_level",
            "low"
        )

        scoring_method = match.get(
            "scoring_method",
            "weighted_fallback"
        )

        # ----------------------------------------------
        # Create database match record
        # ----------------------------------------------
        feature_match = FeatureMatch(

            project_id=project_id,

            source_feature_id=
                source_spatial_feature.id,

            target_feature_id=
                target_spatial_feature.id,

            spatial_score=
                match["spatial_score"],

            attribute_score=
                match["attribute_score"],

            geometry_similarity=
                match["geometry_similarity"],

            proximity_score=
                match["proximity_score"],

            distance=
                match["distance"],

            final_confidence_score=
                confidence_score,

            match_status="suggested",

            explanation=json.dumps(
                {
                    "attribute_comparisons":
                        match.get(
                            "attribute_comparisons"
                        ),

                    "source_index":
                        source_index,

                    "target_index":
                        target_index,

                    "scoring_method":
                        scoring_method,

                    "confidence_level":
                        confidence_level,

                    "ml_confidence":
                        confidence_score,

                    "distance_meters":
                        match.get("distance_meters"),

                    "distance_unit": "meters",

                    "projected_crs":
                        match.get("projected_crs"),

                    "area_similarity":
                        match.get("area_similarity"),
                },
                default=str
            )
        )

        db.add(feature_match)

        saved_matches.append(
            {
                "source_feature_id":
                    source_spatial_feature.id,

                "target_feature_id":
                    target_spatial_feature.id,

                "confidence":
                    confidence_score,

                "confidence_level":
                    confidence_level,

                "scoring_method":
                    scoring_method
            }
        )

    db.commit()

    # --------------------------------------------------
    # 11. Return result
    # --------------------------------------------------
    return {
        "status": "completed",

        "project_id":
            project_id,

        "source_dataset_id":
            source_dataset_id,

        "target_dataset_id":
            target_dataset_id,

        "matches_found":
            len(matches),

        "matches_saved":
            len(saved_matches),

        "matches":
            saved_matches
    }