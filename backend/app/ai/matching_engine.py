from typing import Dict, List
import os
import joblib
import pandas as pd

from app.ai.spatial_matcher import find_spatial_matches
from app.ai.attribute_matcher import find_attribute_matches
from app.ai.confidence_service import build_confidence_result


MODEL_PATH = "processed/ml_models/feature_match_model.pkl"


def combine_match_scores(
    spatial_score: float,
    attribute_score: float,
    spatial_weight: float = 0.6,
    attribute_weight: float = 0.4
) -> float:

    final_score = (
        spatial_score * spatial_weight
        + attribute_score * attribute_weight
    )

    return round(
        max(0.0, min(1.0, final_score)),
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
    distance: float
) -> float:

    if model is None:
        return combine_match_scores(
            spatial_score=spatial_score,
            attribute_score=attribute_score
        )

    distance_score = 1.0 / (
        1.0 + float(distance or 0.0)
    )

    combined_score = (
        float(spatial_score or 0.0) * 0.30
        + float(attribute_score or 0.0) * 0.25
        + float(geometry_similarity or 0.0) * 0.20
        + float(proximity_score or 0.0) * 0.15
        + distance_score * 0.10
    )

    features = pd.DataFrame([
        {
            "spatial_score": float(
                spatial_score or 0.0
            ),
            "attribute_score": float(
                attribute_score or 0.0
            ),
            "geometry_similarity": float(
                geometry_similarity or 0.0
            ),
            "proximity_score": float(
                proximity_score or 0.0
            ),
            "distance": float(
                distance or 0.0
            ),
            "distance_score": distance_score,
            "combined_score": combined_score
        }
    ])

    try:

        probability = model.predict_proba(
            features
        )[0][1]

        return round(
            max(
                0.0,
                min(
                    1.0,
                    float(probability)
                )
            ),
            4
        )

    except Exception:

        return combine_match_scores(
            spatial_score=spatial_score,
            attribute_score=attribute_score
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

    # Resolve legacy degree-based threshold gracefully
    threshold_m = distance_threshold_meters

    spatial_matches = find_spatial_matches(
        source_gdf=source_gdf,
        target_gdf=target_gdf,
        distance_threshold_meters=threshold_m
    )

    attribute_matches = find_attribute_matches(
        source_features=source_features,
        target_features=target_features
    )

    attribute_lookup = {
        match["source_index"]: match
        for match in attribute_matches
    }

    model = load_match_model()

    intelligent_matches = []

    for spatial_match in spatial_matches:

        source_index = spatial_match["source_index"]
        target_index = spatial_match["target_index"]

        attribute_match = attribute_lookup.get(source_index)

        attribute_score = 0.0
        attribute_details = None

        if (
            attribute_match
            and attribute_match["target_index"] == target_index
        ):
            attribute_score = attribute_match["attribute_score"]
            attribute_details = attribute_match["comparisons"]

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
            distance=distance_m
        )

        confidence = build_confidence_result(final_score)

        scoring_method = (
            "random_forest_ml" if model is not None else "weighted_fallback"
        )

        intelligent_matches.append(
            {
                "source_index": source_index,
                "target_index": target_index,
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