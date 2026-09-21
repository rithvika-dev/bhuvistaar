from difflib import SequenceMatcher
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.attribute_mapping import AttributeMapping


from app.services.value_normalizer import get_canonical_field_name

def normalize_field_name(field_name: str) -> str:
    return get_canonical_field_name(field_name)


def calculate_field_similarity(
    source_field: str,
    target_field: str
) -> float:

    source = normalize_field_name(source_field)
    target = normalize_field_name(target_field)

    if source == target:
        return 1.0

    return round(
        SequenceMatcher(
            None,
            source,
            target
        ).ratio(),
        4
    )


def determine_mapping_type(
    similarity: float
) -> str:

    if similarity >= 0.90:
        return "exact"

    if similarity >= 0.70:
        return "strong_similarity"

    if similarity >= 0.50:
        return "possible_match"

    return "weak_match"


def suggest_attribute_mappings(
    db: Session,
    project_id: int,
    source_dataset_id: int,
    target_dataset_id: int,
    source_fields: List[str],
    target_fields: List[str]
) -> dict:

    source_dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == source_dataset_id,
            Dataset.project_id == project_id
        )
        .first()
    )

    if not source_dataset:
        raise ValueError(
            "Source dataset not found"
        )

    target_dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == target_dataset_id,
            Dataset.project_id == project_id
        )
        .first()
    )

    if not target_dataset:
        raise ValueError(
            "Target dataset not found"
        )

    suggestions = []

    for source_field in source_fields:

        best_target = None
        best_score = 0.0

        for target_field in target_fields:

            similarity = calculate_field_similarity(
                source_field,
                target_field
            )

            if similarity > best_score:
                best_score = similarity
                best_target = target_field

        if best_target is None:
            continue

        mapping_type = determine_mapping_type(
            best_score
        )

        mapping = AttributeMapping(
            project_id=project_id,
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id,
            source_field=source_field,
            target_field=best_target,
            mapping_type=mapping_type,
            confidence_score=best_score,
            mapping_status="suggested",
            notes=(
                "Automatically suggested using "
                "field-name similarity."
            )
        )

        db.add(mapping)

        suggestions.append(
            {
                "source_field": source_field,
                "target_field": best_target,
                "mapping_type": mapping_type,
                "confidence_score": best_score
            }
        )

    db.commit()

    return {
        "status": "completed",
        "project_id": project_id,
        "source_dataset_id": source_dataset_id,
        "target_dataset_id": target_dataset_id,
        "mapping_count": len(suggestions),
        "mappings": suggestions
    }