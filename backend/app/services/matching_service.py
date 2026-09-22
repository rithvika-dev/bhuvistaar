import json
import logging
import os
from typing import Optional

import geopandas as gpd
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.spatial_feature import SpatialFeature
from app.models.feature_match import FeatureMatch

from app.ai.matching_engine import find_intelligent_matches
from app.gis.feature_extractor import extract_features

logger = logging.getLogger(__name__)


def resolve_matching_datasets(
    db: Session,
    project_id: int,
    source_dataset_id: Optional[int] = None,
    target_dataset_id: Optional[int] = None
):
    """
    Resolve source (baseline/cadastral) and target (drone/survey) datasets
    for feature matching.  When explicit IDs are provided and valid, uses them.
    Otherwise auto-resolves from project datasets using name/source heuristics
    (same pattern as change_detection_service.resolve_project_versions).
    """
    # 1. Try explicit IDs first
    if source_dataset_id and target_dataset_id and source_dataset_id != target_dataset_id:
        src = (
            db.query(Dataset)
            .filter(Dataset.id == source_dataset_id, Dataset.project_id == project_id)
            .first()
        )
        tgt = (
            db.query(Dataset)
            .filter(Dataset.id == target_dataset_id, Dataset.project_id == project_id)
            .first()
        )
        if src and tgt:
            # Verify they have processed versions with features
            src_v = _get_latest_version_with_features(db, src.id)
            tgt_v = _get_latest_version_with_features(db, tgt.id)
            if src_v and tgt_v:
                logger.info(
                    "Using explicit dataset IDs: source=%d (version %d), target=%d (version %d)",
                    src.id, src_v.id, tgt.id, tgt_v.id
                )
                return src, tgt, src_v, tgt_v

    # 2. Auto-resolve from project datasets
    datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id)
        .order_by(Dataset.created_at.asc())
        .all()
    )

    if not datasets:
        raise ValueError(f"No datasets found for project {project_id}.")

    # Collect datasets with their latest version containing spatial features
    candidates = []
    for d in datasets:
        v = _get_latest_version_with_features(db, d.id)
        if v:
            count = db.query(SpatialFeature).filter(
                SpatialFeature.dataset_version_id == v.id
            ).count()
            candidates.append((d, v, count))

    if len(candidates) < 2:
        raise ValueError(
            f"Project {project_id} requires at least 2 processed datasets with spatial features. "
            f"Found {len(candidates)} valid datasets."
        )

    # Separate baseline vs drone/survey by name/source heuristics
    baseline_candidate = None
    drone_candidate = None

    for d, v, cnt in candidates:
        name_lower = (d.name or "").lower()
        source_lower = (d.source or "").lower()

        if (
            "cadastral" in name_lower
            or "baseline" in name_lower
            or "cadastral" in source_lower
            or "historical" in source_lower
            or "t0" in name_lower
        ) and not baseline_candidate:
            baseline_candidate = (d, v, cnt)
        elif (
            "drone" in name_lower
            or "footprint" in name_lower
            or "building" in name_lower
            or "survey" in source_lower
            or "drone" in source_lower
            or "t1" in name_lower
        ) and not drone_candidate:
            drone_candidate = (d, v, cnt)

    # Fallbacks if naming didn't match cleanly
    if not baseline_candidate:
        baseline_candidate = candidates[0]
    if not drone_candidate:
        remaining = [c for c in candidates if c[1].id != baseline_candidate[1].id]
        if remaining:
            drone_candidate = remaining[-1]
        else:
            drone_candidate = candidates[-1]

    if baseline_candidate[1].id == drone_candidate[1].id:
        raise ValueError("Source and target dataset versions must be distinct.")

    d_src, v_src, _ = baseline_candidate
    d_tgt, v_tgt, _ = drone_candidate

    logger.info(
        "Auto-resolved datasets for project %d: source=%s (dataset %d, version %d), "
        "target=%s (dataset %d, version %d)",
        project_id, d_src.name, d_src.id, v_src.id, d_tgt.name, d_tgt.id, v_tgt.id
    )

    return d_src, d_tgt, v_src, v_tgt


def _get_latest_version_with_features(db: Session, dataset_id: int):
    """Get the latest DatasetVersion for a dataset that has spatial features."""
    versions = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .all()
    )
    for v in versions:
        count = db.query(SpatialFeature).filter(
            SpatialFeature.dataset_version_id == v.id
        ).count()
        if count > 0:
            return v
    return None


def run_feature_matching(
    db: Session,
    project_id: int,
    source_dataset_id: Optional[int] = None,
    target_dataset_id: Optional[int] = None
) -> dict:

    # --------------------------------------------------
    # 1. Resolve source & target datasets + versions
    #    (auto-resolves if IDs are None or invalid)
    # --------------------------------------------------
    source_dataset, target_dataset, source_version, target_version = (
        resolve_matching_datasets(
            db, project_id, source_dataset_id, target_dataset_id
        )
    )

    # Update IDs from resolved datasets
    source_dataset_id = source_dataset.id
    target_dataset_id = target_dataset.id

    logger.info(
        "Matching: source dataset=%d (%s) version=%d, "
        "target dataset=%d (%s) version=%d",
        source_dataset_id, source_dataset.name, source_version.id,
        target_dataset_id, target_dataset.name, target_version.id
    )

    # --------------------------------------------------
    # 2. Check uploaded files
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
    # 3. Delete existing matches for this project
    #    (idempotent: avoids unique constraint violations
    #     on idx_feature_matches_unique_pair)
    # --------------------------------------------------
    deleted_count = (
        db.query(FeatureMatch)
        .filter(FeatureMatch.project_id == project_id)
        .delete(synchronize_session=False)
    )
    if deleted_count:
        logger.info(
            "Deleted %d existing matches for project %d before re-matching",
            deleted_count, project_id
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
                    "identity_score":
                        match.get("identity_score", 0.5),

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