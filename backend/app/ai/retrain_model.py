import os

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from app.ai.review_training_data import collect_reviewed_matches


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


def retrain_from_reviews(
    db,
    project_id: int
) -> dict:

    # --------------------------------------------------
    # 1. Collect human-reviewed matches
    # --------------------------------------------------
    dataset = collect_reviewed_matches(
        db=db,
        project_id=project_id
    )

    # --------------------------------------------------
    # 2. Check training data
    # --------------------------------------------------
    if dataset.empty:

        return {
            "status": "no_training_data",
            "project_id": project_id,
            "message": (
                "No approved or rejected "
                "feature matches are available "
                "for training."
            )
        }

    # --------------------------------------------------
    # 3. Check both classes
    # --------------------------------------------------
    unique_labels = dataset[
        "label"
    ].unique()

    if len(unique_labels) < 2:

        return {
            "status":
                "insufficient_classes",

            "project_id":
                project_id,

            "message": (
                "Training requires both "
                "approved and rejected matches."
            ),

            "available_labels":
                [
                    int(label)
                    for label in unique_labels
                ]
        }

    # --------------------------------------------------
    # 4. Prepare features and labels
    # --------------------------------------------------
    X = dataset[
        FEATURE_COLUMNS
    ]

    y = dataset["label"]

    approved_count = int(
        (dataset["label"] == 1).sum()
    )

    rejected_count = int(
        (dataset["label"] == 0).sum()
    )

    # --------------------------------------------------
    # 5. Handle very small datasets
    # --------------------------------------------------
    if len(dataset) < 4:

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            class_weight="balanced"
        )

        model.fit(
            X,
            y
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
            "status":
                "completed",

            "project_id":
                project_id,

            "model_type":
                "RandomForestClassifier",

            "training_samples":
                len(dataset),

            "testing_samples":
                0,

            "reviewed_matches":
                len(dataset),

            "approved_matches":
                approved_count,

            "rejected_matches":
                rejected_count,

            "accuracy":
                None,

            "model_path":
                MODEL_PATH,

            "message": (
                "Model trained using "
                "human-reviewed matches. "
                "The dataset is currently "
                "too small for reliable "
                "evaluation."
            )
        }

    # --------------------------------------------------
    # 6. Split training and testing data
    # --------------------------------------------------
    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y
        )
    )

    # --------------------------------------------------
    # 7. Train Random Forest
    # --------------------------------------------------
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------
    # 8. Evaluate model
    # --------------------------------------------------
    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    # --------------------------------------------------
    # 9. Save model
    # --------------------------------------------------
    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    # --------------------------------------------------
    # 10. Return training information
    # --------------------------------------------------
    return {
        "status":
            "completed",

        "project_id":
            project_id,

        "model_type":
            "RandomForestClassifier",

        "training_samples":
            len(X_train),

        "testing_samples":
            len(X_test),

        "reviewed_matches":
            len(dataset),

        "approved_matches":
            approved_count,

        "rejected_matches":
            rejected_count,

        "accuracy":
            round(
                float(accuracy),
                4
            ),

        "model_path":
            MODEL_PATH,

        "message": (
            "ML model retrained successfully "
            "using human-reviewed matches."
        )
    }