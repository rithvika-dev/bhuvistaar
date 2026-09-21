import pandas as pd
from sqlalchemy.orm import Session

from app.models.feature_match import FeatureMatch


FEATURE_COLUMNS = [
    "spatial_score",
    "attribute_score",
    "geometry_similarity",
    "proximity_score",
    "distance",
    "distance_score",
    "combined_score"
]


def collect_reviewed_matches(
    db: Session,
    project_id: int
) -> pd.DataFrame:

    matches = (
        db.query(FeatureMatch)
        .filter(
            FeatureMatch.project_id == project_id,
            FeatureMatch.match_status.in_(
                ["approved", "rejected"]
            )
        )
        .all()
    )

    rows = []

    for match in matches:

        if match.match_status == "approved":
            label = 1
        elif match.match_status == "rejected":
            label = 0
        else:
            continue

        spatial_score = float(
            match.spatial_score or 0.0
        )

        attribute_score = float(
            match.attribute_score or 0.0
        )

        geometry_similarity = float(
            match.geometry_similarity or 0.0
        )

        proximity_score = float(
            match.proximity_score or 0.0
        )

        distance = float(
            match.distance or 0.0
        )

        distance_score = 1.0 / (
            1.0 + distance
        )

        combined_score = (
            spatial_score * 0.30
            + attribute_score * 0.25
            + geometry_similarity * 0.20
            + proximity_score * 0.15
            + distance_score * 0.10
        )

        rows.append(
            {
                "spatial_score":
                    spatial_score,

                "attribute_score":
                    attribute_score,

                "geometry_similarity":
                    geometry_similarity,

                "proximity_score":
                    proximity_score,

                "distance":
                    distance,

                "distance_score":
                    distance_score,

                "combined_score":
                    combined_score,

                "label":
                    label
            }
        )

    dataframe = pd.DataFrame(rows)

    return dataframe


def get_review_training_summary(
    db: Session,
    project_id: int
) -> dict:

    dataframe = collect_reviewed_matches(
        db=db,
        project_id=project_id
    )

    if dataframe.empty:

        return {
            "status":
                "no_reviewed_matches",

            "project_id":
                project_id,

            "total_reviewed":
                0,

            "approved":
                0,

            "rejected":
                0,

            "ready_for_training":
                False
        }

    approved_count = int(
        (
            dataframe["label"] == 1
        ).sum()
    )

    rejected_count = int(
        (
            dataframe["label"] == 0
        ).sum()
    )

    total_reviewed = len(dataframe)

    ready_for_training = (
        approved_count > 0
        and rejected_count > 0
    )

    return {
        "status":
            "completed",

        "project_id":
            project_id,

        "total_reviewed":
            total_reviewed,

        "approved":
            approved_count,

        "rejected":
            rejected_count,

        "ready_for_training":
            ready_for_training
    }