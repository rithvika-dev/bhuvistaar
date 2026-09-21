from typing import Dict, List, Any
from difflib import SequenceMatcher


def normalize_value(value: Any) -> str:
    """
    Convert an attribute value into a normalized string.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def calculate_string_similarity(
    value_a: Any,
    value_b: Any
) -> float:
    """
    Calculate similarity between two attribute values.

    Returns a score between 0 and 1.
    """

    a = normalize_value(value_a)
    b = normalize_value(value_b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(None, a, b).ratio()


def calculate_numeric_similarity(
    value_a: Any,
    value_b: Any
) -> float:
    """
    Calculate similarity between two numeric values.
    """

    try:
        a = float(value_a)
        b = float(value_b)
    except (TypeError, ValueError):
        return 0.0

    if a == b:
        return 1.0

    maximum = max(abs(a), abs(b))

    if maximum == 0:
        return 1.0

    difference = abs(a - b)

    return max(
        0.0,
        1.0 - (difference / maximum)
    )


def compare_attributes(
    source_attributes: Dict,
    target_attributes: Dict
) -> Dict:
    """
    Compare attributes between two GIS features.
    """

    comparisons: List[Dict] = []

    common_fields = set(source_attributes.keys()).intersection(
        target_attributes.keys()
    )

    if not common_fields:
        return {
            "matched_fields": 0,
            "attribute_score": 0.0,
            "comparisons": []
        }

    total_score = 0.0

    for field in common_fields:

        source_value = source_attributes[field]
        target_value = target_attributes[field]

        if isinstance(source_value, (int, float)) and isinstance(
            target_value, (int, float)
        ):
            similarity = calculate_numeric_similarity(
                source_value,
                target_value
            )
        else:
            similarity = calculate_string_similarity(
                source_value,
                target_value
            )

        comparisons.append(
            {
                "field": field,
                "source_value": source_value,
                "target_value": target_value,
                "similarity": round(similarity, 4)
            }
        )

        total_score += similarity

    attribute_score = total_score / len(common_fields)

    return {
        "matched_fields": len(common_fields),
        "attribute_score": round(attribute_score, 4),
        "comparisons": comparisons
    }


def find_attribute_matches(
    source_features: List[Dict],
    target_features: List[Dict]
) -> List[Dict]:
    """
    Find the best attribute match for every source feature.
    """

    matches = []

    for source in source_features:

        source_attributes = source.get(
            "attributes",
            {}
        )

        best_match = None
        best_score = 0.0

        for target in target_features:

            target_attributes = target.get(
                "attributes",
                {}
            )

            comparison = compare_attributes(
                source_attributes,
                target_attributes
            )

            score = comparison["attribute_score"]

            if score > best_score:

                best_score = score

                best_match = {
                    "source_index": source.get("source_index"),
                    "target_index": target.get("source_index"),
                    "attribute_score": score,
                    "matched_fields": comparison["matched_fields"],
                    "comparisons": comparison["comparisons"]
                }

        if best_match:
            matches.append(best_match)

    return matches