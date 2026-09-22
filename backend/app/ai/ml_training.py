import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from app.ai.ml_feature_engineering import build_training_row


MODEL_DIR = "processed/ml_models"
MODEL_PATH = os.path.join(
    MODEL_DIR,
    "feature_match_model.pkl"
)


FEATURE_COLUMNS = [
    "identity_score",
    "spatial_score",
    "attribute_score",
    "geometry_similarity",
    "proximity_score",
    "distance",
    "distance_score",
    "combined_score"
]


def create_training_dataset() -> pd.DataFrame:
    """
    Create a robust, domain-balanced GIS training dataset.
    Covers legal cadastral matching scenarios:
    - Same parcel_id + spatial proximity (even with footprint/parcel area ratio or landuse change)
    - High spatial overlap + attribute agreement
    - Conflicting parcel IDs (cross-parcel mismatches)
    - Far distances / non-overlapping features
    """

    training_rows = [
        # 1. Perfect matches (exact parcel_id, high spatial, high attributes)
        build_training_row(spatial_score=0.95, attribute_score=0.95, geometry_similarity=0.92, proximity_score=0.98, distance=0.5, identity_score=1.0, label=1),
        build_training_row(spatial_score=0.90, attribute_score=0.92, geometry_similarity=0.88, proximity_score=0.95, distance=1.2, identity_score=1.0, label=1),
        build_training_row(spatial_score=0.85, attribute_score=0.88, geometry_similarity=0.82, proximity_score=0.92, distance=2.0, identity_score=1.0, label=1),

        # 2. Exact parcel_id with area differences (e.g. building footprint 150 sqm vs parcel 1500 sqm, Match #170)
        build_training_row(spatial_score=0.40, attribute_score=0.67, geometry_similarity=0.18, proximity_score=0.94, distance=2.8, identity_score=1.0, label=1),
        build_training_row(spatial_score=0.45, attribute_score=0.70, geometry_similarity=0.25, proximity_score=0.90, distance=3.5, identity_score=1.0, label=1),
        build_training_row(spatial_score=0.38, attribute_score=0.65, geometry_similarity=0.15, proximity_score=0.92, distance=2.5, identity_score=1.0, label=1),

        # 3. Exact parcel_id with land-use change over time (e.g. agricultural -> residential)
        build_training_row(spatial_score=0.55, attribute_score=0.68, geometry_similarity=0.40, proximity_score=0.88, distance=4.5, identity_score=1.0, label=1),
        build_training_row(spatial_score=0.60, attribute_score=0.72, geometry_similarity=0.50, proximity_score=0.85, distance=5.0, identity_score=1.0, label=1),

        # 4. Partial identity match (e.g. "1025" in "1025/1") with good spatial alignment
        build_training_row(spatial_score=0.75, attribute_score=0.80, geometry_similarity=0.70, proximity_score=0.85, distance=4.0, identity_score=0.85, label=1),
        build_training_row(spatial_score=0.80, attribute_score=0.85, geometry_similarity=0.75, proximity_score=0.90, distance=3.0, identity_score=0.85, label=1),

        # 5. Missing identity but strong spatial overlap + attribute agreement (un-parceled GIS features)
        build_training_row(spatial_score=0.88, attribute_score=0.85, geometry_similarity=0.85, proximity_score=0.95, distance=1.0, identity_score=0.5, label=1),
        build_training_row(spatial_score=0.82, attribute_score=0.80, geometry_similarity=0.80, proximity_score=0.90, distance=2.5, identity_score=0.5, label=1),

        # 6. Conflicting parcel_id (e.g. P001 vs P002 adjacent parcels) -> NEVER match
        build_training_row(spatial_score=0.45, attribute_score=0.15, geometry_similarity=0.30, proximity_score=0.90, distance=3.0, identity_score=0.0, label=0),
        build_training_row(spatial_score=0.55, attribute_score=0.20, geometry_similarity=0.45, proximity_score=0.85, distance=5.0, identity_score=0.0, label=0),
        build_training_row(spatial_score=0.65, attribute_score=0.20, geometry_similarity=0.55, proximity_score=0.80, distance=6.0, identity_score=0.0, label=0),
        build_training_row(spatial_score=0.35, attribute_score=0.10, geometry_similarity=0.20, proximity_score=0.92, distance=2.0, identity_score=0.0, label=0),

        # 7. Far distances / non-overlapping parcels
        build_training_row(spatial_score=0.15, attribute_score=0.20, geometry_similarity=0.05, proximity_score=0.30, distance=35.0, identity_score=0.0, label=0),
        build_training_row(spatial_score=0.10, attribute_score=0.15, geometry_similarity=0.00, proximity_score=0.20, distance=45.0, identity_score=0.5, label=0),
        build_training_row(spatial_score=0.20, attribute_score=0.25, geometry_similarity=0.10, proximity_score=0.40, distance=28.0, identity_score=0.5, label=0),
        build_training_row(spatial_score=0.25, attribute_score=0.30, geometry_similarity=0.15, proximity_score=0.50, distance=22.0, identity_score=0.5, label=0),

        # 8. Unrelated features (low spatial + low attributes)
        build_training_row(spatial_score=0.10, attribute_score=0.10, geometry_similarity=0.02, proximity_score=0.15, distance=48.0, identity_score=0.0, label=0),
        build_training_row(spatial_score=0.18, attribute_score=0.22, geometry_similarity=0.08, proximity_score=0.35, distance=32.0, identity_score=0.0, label=0),
    ]

    return pd.DataFrame(training_rows)


def train_feature_match_model() -> dict:
    """
    Train and save the feature matching model.
    """

    dataset = create_training_dataset()

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    return {
        "status": "completed",
        "model_type": "RandomForestClassifier",
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "accuracy": round(float(accuracy), 4),
        "model_path": MODEL_PATH
    }