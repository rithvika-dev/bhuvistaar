from typing import Dict, List, Any, Tuple, Optional
from difflib import SequenceMatcher
import re


# Provenance and metadata fields that must NOT penalize attribute match score
IGNORED_METADATA_FIELDS = {
    "source", "source_name", "dataset", "dataset_name", "dataset_type", "layer", "layer_name",
    "survey_year", "survey_date", "acquisition_date", "capture_date", "created_at", "updated_at",
    "timestamp", "file_name", "file_path", "crs", "srid", "gid", "objectid", "fid", "id",
    "feature_id", "building_id", "status"
}

# Strong legal identity fields
IDENTITY_FIELDS = {
    "parcel_id", "ulpin", "khasra_no", "khasra_num", "survey_number", "survey_no", "survey_num",
    "subdivision_number", "land_record_id", "source_record_id", "plot_number", "plot_no",
    "property_tax_id", "tax_id"
}

# Categorical planning / land-use fields
CATEGORICAL_FIELDS = {
    "land_use", "landuse", "ownership_type", "owner_type", "property_type", "zoning", "tenure"
}

# Numeric measurement fields
NUMERIC_MEASUREMENT_FIELDS = {
    "area_sq_m", "area_sqm", "area", "builtup_area", "footprint_area", "constructed_area",
    "perimeter", "height", "floors"
}


def normalize_value(value: Any) -> str:
    """Convert an attribute value into a normalized string."""
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_identity_code(value: Any) -> str:
    """Normalize parcel / identity code by removing punctuation, spaces, and casing."""
    if value is None:
        return ""
    raw = str(value).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", raw)


def calculate_string_similarity(value_a: Any, value_b: Any) -> float:
    """Calculate similarity between two attribute values [0, 1]."""
    a = normalize_value(value_a)
    b = normalize_value(value_b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(None, a, b).ratio()


def calculate_numeric_similarity(value_a: Any, value_b: Any) -> float:
    """
    Calculate proportional similarity between two numeric values.
    Returns ratio min(a,b) / max(a,b) smoothly mapped to [0, 1].
    """
    try:
        clean_a = re.sub(r"[^\d.-]", "", str(value_a))
        clean_b = re.sub(r"[^\d.-]", "", str(value_b))
        a = float(clean_a)
        b = float(clean_b)
    except (TypeError, ValueError):
        return 0.0

    if a == b:
        return 1.0

    maximum = max(abs(a), abs(b))
    if maximum == 0:
        return 1.0

    minimum = min(abs(a), abs(b))
    # Direct ratio min/max (e.g. 150/1500 = 0.10; 1000/1020 = 0.98)
    ratio = minimum / maximum
    return max(0.0, min(1.0, ratio))


def calculate_identity_score(
    source_attributes: Dict,
    target_attributes: Dict
) -> Tuple[float, Optional[str], Optional[str], Optional[str]]:
    """
    Evaluates agreement on legal land-record identifiers (parcel_id, khasra_no, ulpin).
    Returns (identity_score, matched_field, src_val, tgt_val):
      1.0 = Exact identity match
      0.85 = Partial / normalized substring match
      0.0 = Conflicting identity (different non-empty parcel_id values on both sides)
      0.5 = Identity missing on one or both sides (neutral)
    """
    src_clean = {k.lower(): (k, v) for k, v in source_attributes.items() if v is not None and str(v).strip()}
    tgt_clean = {k.lower(): (k, v) for k, v in target_attributes.items() if v is not None and str(v).strip()}

    # Check common identity fields
    for field in IDENTITY_FIELDS:
        if field in src_clean and field in tgt_clean:
            _, src_val = src_clean[field]
            _, tgt_val = tgt_clean[field]

            norm_src = normalize_identity_code(src_val)
            norm_tgt = normalize_identity_code(tgt_val)

            if not norm_src or not norm_tgt:
                continue

            if norm_src == norm_tgt:
                return 1.0, field, str(src_val), str(tgt_val)

            # Substring / partial match (e.g. "1025" in "1025/2")
            if norm_src in norm_tgt or norm_tgt in norm_src:
                return 0.85, field, str(src_val), str(tgt_val)

            # Conflicting identity
            return 0.0, field, str(src_val), str(tgt_val)

    # Cross-field identity check (e.g. source has parcel_id, target has khasra_no)
    src_id_vals = [v for k, v in source_attributes.items() if k.lower() in IDENTITY_FIELDS and v is not None and str(v).strip()]
    tgt_id_vals = [v for k, v in target_attributes.items() if k.lower() in IDENTITY_FIELDS and v is not None and str(v).strip()]

    if src_id_vals and tgt_id_vals:
        for s_val in src_id_vals:
            norm_s = normalize_identity_code(s_val)
            for t_val in tgt_id_vals:
                norm_t = normalize_identity_code(t_val)
                if norm_s and norm_t:
                    if norm_s == norm_t:
                        return 1.0, "cross_identity", str(s_val), str(t_val)
                    if norm_s in norm_t or norm_t in norm_s:
                        return 0.85, "cross_identity", str(s_val), str(t_val)
        # Present on both sides but no match found
        return 0.0, "identity_mismatch", str(src_id_vals[0]), str(tgt_id_vals[0])

    # Missing on one or both sides -> Neutral
    return 0.5, None, None, None


def compare_attributes(
    source_attributes: Dict,
    target_attributes: Dict
) -> Dict:
    """
    Compare attributes between two GIS features with domain-aware weighting.
    Ignores metadata fields (source, survey_year) and properly handles
    identity, land-use, and area measurements.
    """
    comparisons: List[Dict] = []

    # 1. Identity scoring
    identity_score, id_field, id_src, id_tgt = calculate_identity_score(
        source_attributes,
        target_attributes
    )

    if id_field:
        comparisons.append({
            "field": id_field,
            "source_value": id_src,
            "target_value": id_tgt,
            "similarity": identity_score,
            "is_identity": True
        })

    # 2. Filter common fields excluding metadata
    common_fields = [
        f for f in set(source_attributes.keys()).intersection(target_attributes.keys())
        if f.lower() not in IGNORED_METADATA_FIELDS
    ]

    total_weighted_score = 0.0
    total_weight = 0.0

    for field in common_fields:
        field_lower = field.lower()
        source_value = source_attributes[field]
        target_value = target_attributes[field]

        if field_lower in IDENTITY_FIELDS:
            # Identity is weighted separately
            continue

        if field_lower in NUMERIC_MEASUREMENT_FIELDS:
            similarity = calculate_numeric_similarity(source_value, target_value)
            weight = 0.35
        elif field_lower in CATEGORICAL_FIELDS:
            norm_s = normalize_value(source_value)
            norm_t = normalize_value(target_value)
            if norm_s == norm_t:
                similarity = 1.0
            else:
                # Disagreement on land_use reduces attribute score proportionally
                similarity = 0.25
            weight = 0.40
        else:
            similarity = calculate_string_similarity(source_value, target_value)
            weight = 0.25

        comparisons.append({
            "field": field,
            "source_value": source_value,
            "target_value": target_value,
            "similarity": round(similarity, 4),
            "is_identity": False
        })

        total_weighted_score += similarity * weight
        total_weight += weight

    if total_weight > 0:
        non_id_score = total_weighted_score / total_weight
    else:
        non_id_score = 0.5  # Neutral if no other attributes

    # Combine identity score and attribute score
    if identity_score == 1.0:
        # Exact parcel_id match provides a strong baseline
        attribute_score = 0.60 * identity_score + 0.40 * non_id_score
    elif identity_score == 0.85:
        attribute_score = 0.55 * identity_score + 0.45 * non_id_score
    elif identity_score == 0.0:
        # Conflicting identity heavily penalizes attribute score
        attribute_score = 0.20 * non_id_score
    else:
        # Neutral identity -> purely non_id attributes
        attribute_score = non_id_score

    return {
        "matched_fields": len(comparisons),
        "identity_score": round(identity_score, 4),
        "attribute_score": round(attribute_score, 4),
        "comparisons": comparisons
    }


def find_attribute_matches(
    source_features: List[Dict],
    target_features: List[Dict]
) -> List[Dict]:
    """Find the best attribute match for every source feature."""
    matches = []

    for source in source_features:
        source_attributes = source.get("attributes", {})
        best_match = None
        best_score = -1.0

        for target in target_features:
            target_attributes = target.get("attributes", {})
            comparison = compare_attributes(source_attributes, target_attributes)
            score = comparison["attribute_score"]

            if score > best_score:
                best_score = score
                best_match = {
                    "source_index": source.get("source_index"),
                    "target_index": target.get("source_index"),
                    "attribute_score": score,
                    "identity_score": comparison["identity_score"],
                    "matched_fields": comparison["matched_fields"],
                    "comparisons": comparison["comparisons"]
                }

        if best_match:
            matches.append(best_match)

    return matches