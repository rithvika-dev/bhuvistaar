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


def create_training_dataset() -> pd.DataFrame:
    """
    Create a small initial training dataset.

    These examples are demonstration data.
    Later, reviewed real-world matches can be
    used to retrain the model.
    """

    training_rows = [

        # Correct matches
        build_training_row(
            0.95, 0.94, 0.92, 0.93, 0.0002, 1
        ),

        build_training_row(
            0.91, 0.90, 0.88, 0.89, 0.0005, 1
        ),

        build_training_row(
            0.87, 0.92, 0.85, 0.88, 0.0008, 1
        ),

        build_training_row(
            0.82, 0.86, 0.80, 0.84, 0.0010, 1
        ),

        build_training_row(
            0.78, 0.81, 0.76, 0.80, 0.0015, 1
        ),

        build_training_row(
            0.74, 0.79, 0.72, 0.76, 0.0020, 1
        ),

        # Incorrect matches
        build_training_row(
            0.20, 0.15, 0.12, 0.18, 0.0200, 0
        ),

        build_training_row(
            0.30, 0.22, 0.18, 0.25, 0.0150, 0
        ),

        build_training_row(
            0.35, 0.28, 0.30, 0.32, 0.0120, 0
        ),

        build_training_row(
            0.40, 0.31, 0.25, 0.35, 0.0100, 0
        ),

        build_training_row(
            0.45, 0.38, 0.35, 0.40, 0.0080, 0
        ),

        build_training_row(
            0.50, 0.42, 0.40, 0.45, 0.0060, 0
        ),
    ]

    return pd.DataFrame(training_rows)


def train_feature_match_model() -> dict:
    """
    Train and save the feature matching model.
    """

    dataset = create_training_dataset()

    feature_columns = [
        "spatial_score",
        "attribute_score",
        "geometry_similarity",
        "proximity_score",
        "distance",
        "distance_score",
        "combined_score"
    ]

    X = dataset[feature_columns]
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
        random_state=42
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