from typing import Dict, List, Optional
import os
import joblib
import pandas as pd

from app.ai.spatial_matcher import find_spatial_matches
from app.ai.attribute_matcher import compare_attributes, find_attribute_matches
from app.ai.ml_feature_engineering import build_match_features
from app.ai.confidence_service import build_confidence_result


MODEL_PATH = "processed/ml_models/feature_match_model.pkl"


def combine_match_scores(
    spatial_score: float,
    attribute_score: float,
    identity_score: float = 0.5,
    geometry_similarity: float = 0.0,
    proximity_score: float = 0.0,
) -> float:
    """
    Domain-aware fallback score calculation when ML model is not available.
    """
    if identity_score == 1.0:
        # Strong identity anchor
        final = 0.45 * identity_score + 0.25 * spatial_score + 0.20 * attribute_score + 0.10 * proximity_score
    elif identity_score == 0.85:
        final = 0.40 * identity_score + 0.25 * spatial_score + 0.20 * attribute_score + 0.15 * proximity_score
    elif identity_score == 0.0:
        # Conflicting identity heavily lowers confidence
        final = 0.15 * spatial_score + 0.10 * attribute_score
    else:
        # Neutral identity (missing) -> spatial & general attributes dominate
        final = 0.50 * spatial_score + 0.35 * attribute_score + 0.15 * proximity_score

    return round(
        max(0.0, min(1.0, float(final))),
        4
    )


def load_match_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def calculate_ml_confidence(
    model,
    spatial_score: float,
    attribute_score: float,
    geometry_similarity: float,
    proximity_score: float,
    distance: float,
    identity_score: float = 0.5
) -> float:
    """
    Calculate final match confidence using trained RandomForest model,
    falling back to domain-weighted scoring if model is absent or errors.
    """
    if model is None:
        return combine_match_scores(
            spatial_score=spatial_score,
            attribute_score=attribute_score,
            identity_score=identity_score,
            geometry_similarity=geometry_similarity,
            proximity_score=proximity_score
        )

    features_dict = build_match_features(
        spatial_score=spatial_score,
        attribute_score=attribute_score,
        geometry_similarity=geometry_similarity,
        proximity_score=proximity_score,
        distance=distance,
        identity_score=identity_score
    )

    feature_cols = [
        "identity_score",
        "spatial_score",
        "attribute_score",
        "geometry_similarity",
        "proximity_score",
        "distance",
        "distance_score",
        "combined_score"
    ]

    features_df = pd.DataFrame([features_dict])[feature_cols]

    try:
        probability = model.predict_proba(features_df)[0][1]
        return round(
            max(0.0, min(1.0, float(probability))),
            4
        )
    except Exception:
        return combine_match_scores(
            spatial_score=spatial_score,
            attribute_score=attribute_score,
            identity_score=identity_score,
            geometry_similarity=geometry_similarity,
            proximity_score=proximity_score
        )


def find_intelligent_matches(
    source_gdf,
    target_gdf,
    source_features: List[Dict],
    target_features: List[Dict],
    distance_threshold_meters: float = 50.0,
    # Legacy param kept for backward compatibility
    distance_threshold: float = None,
) -> List[Dict]:
    """
    Find intelligent matches between source and target GIS layers.
    Uses metric spatial matching combined with pairwise attribute and identity comparisons.
    """
    threshold_m = distance_threshold_meters

    spatial_matches = find_spatial_matches(
        source_gdf=source_gdf,
        target_gdf=target_gdf,
        distance_threshold_meters=threshold_m
    )

    # Build attribute lookup maps by feature index
    source_attr_map = {
        f.get("source_index", i): f.get("attributes", {})
        for i, f in enumerate(source_features)
    }
    target_attr_map = {
        f.get("source_index", i): f.get("attributes", {})
        for i, f in enumerate(target_features)
    }

    model = load_match_model()

    intelligent_matches = []

    for spatial_match in spatial_matches:
        source_index = spatial_match["source_index"]
        target_index = spatial_match["target_index"]

        src_attrs = source_attr_map.get(source_index, {})
        tgt_attrs = target_attr_map.get(target_index, {})

        # Direct pairwise attribute and legal identity comparison
        comparison = compare_attributes(src_attrs, tgt_attrs)
        attribute_score = comparison["attribute_score"]
        identity_score = comparison["identity_score"]
        attribute_details = comparison["comparisons"]

        spatial_score = spatial_match["confidence_score"]
        geometry_similarity = spatial_match["geometry_similarity"]
        proximity_score = spatial_match["proximity_score"]
        distance_m = spatial_match["distance_meters"]

        final_score = calculate_ml_confidence(
            model=model,
            spatial_score=spatial_score,
            attribute_score=attribute_score,
            geometry_similarity=geometry_similarity,
            proximity_score=proximity_score,
            distance=distance_m,
            identity_score=identity_score
        )

        confidence = build_confidence_result(final_score)

        scoring_method = (
            "random_forest_ml" if model is not None else "weighted_fallback"
        )

        intelligent_matches.append(
            {
                "source_index": source_index,
                "target_index": target_index,
                "identity_score": identity_score,
                "spatial_score": spatial_score,
                "attribute_score": attribute_score,
                "geometry_similarity": geometry_similarity,
                "area_similarity": spatial_match.get("area_similarity", 0.0),
                "proximity_score": proximity_score,
                "distance": distance_m,
                "distance_meters": distance_m,
                "distance_unit": "meters",
                "projected_crs": spatial_match.get("projected_crs"),
                "final_confidence_score": confidence["confidence_score"],
                "confidence_level": confidence["confidence_level"],
                "scoring_method": scoring_method,
                "attribute_comparisons": attribute_details,
            }
        )

    intelligent_matches.sort(
        key=lambda item: item["final_confidence_score"],
        reverse=True
    )

    return intelligent_matches