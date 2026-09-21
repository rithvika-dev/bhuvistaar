from typing import Dict


def build_match_features(
    spatial_score: float,
    attribute_score: float,
    geometry_similarity: float,
    proximity_score: float,
    distance: float
) -> Dict[str, float]:
    """
    Convert GIS matching information into numerical
    features that can be used by an ML model.
    """

    spatial_score = float(spatial_score or 0.0)
    attribute_score = float(attribute_score or 0.0)
    geometry_similarity = float(
        geometry_similarity or 0.0
    )
    proximity_score = float(
        proximity_score or 0.0
    )
    distance = float(distance or 0.0)

    # Distance should contribute less as it increases.
    distance_score = 1.0 / (1.0 + distance)

    # Combined heuristic score.
    combined_score = (
        spatial_score * 0.30
        + attribute_score * 0.25
        + geometry_similarity * 0.20
        + proximity_score * 0.15
        + distance_score * 0.10
    )

    return {
        "spatial_score": spatial_score,
        "attribute_score": attribute_score,
        "geometry_similarity": geometry_similarity,
        "proximity_score": proximity_score,
        "distance": distance,
        "distance_score": distance_score,
        "combined_score": combined_score
    }


def build_training_row(
    spatial_score: float,
    attribute_score: float,
    geometry_similarity: float,
    proximity_score: float,
    distance: float,
    label: int
) -> Dict[str, float]:
    """
    Create one labelled training example.

    label:
        1 = correct match
        0 = incorrect match
    """

    features = build_match_features(
        spatial_score=spatial_score,
        attribute_score=attribute_score,
        geometry_similarity=geometry_similarity,
        proximity_score=proximity_score,
        distance=distance
    )

    features["label"] = int(label)

    return features