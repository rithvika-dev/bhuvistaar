from typing import Dict, Optional


def build_match_features(
    spatial_score: float,
    attribute_score: float,
    geometry_similarity: float,
    proximity_score: float,
    distance: float,
    identity_score: Optional[float] = 0.5
) -> Dict[str, float]:
    """
    Convert GIS matching information into numerical
    features that can be used by an ML model.
    """

    spatial_score = float(spatial_score or 0.0)
    attribute_score = float(attribute_score or 0.0)
    geometry_similarity = float(geometry_similarity or 0.0)
    proximity_score = float(proximity_score or 0.0)
    distance = float(distance or 0.0)
    identity_score = float(0.5 if identity_score is None else identity_score)

    # Distance score decay
    distance_score = 1.0 / (1.0 + (distance / 10.0))

    # Combined heuristic score with strong weight on identity_score
    combined_score = (
        identity_score * 0.35
        + spatial_score * 0.25
        + attribute_score * 0.15
        + geometry_similarity * 0.10
        + proximity_score * 0.10
        + distance_score * 0.05
    )

    return {
        "identity_score": identity_score,
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
    identity_score: float,
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
        distance=distance,
        identity_score=identity_score
    )

    features["label"] = int(label)

    return features