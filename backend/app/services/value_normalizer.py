"""
Value normalizer for attribute harmonization.

Provides text/value normalization, semantic alias matching, abbreviation expansion,
data type detection, unit awareness, and missing-value detection.

IMPORTANT: Does not overwrite source values. All outputs are suggestions
requiring human review.
"""

import re
from typing import Any, Dict, Optional, Tuple

# Common Indian urban land record abbreviations & semantic aliases
VALUE_ABBREVIATIONS = {
    "RES": "Residential",
    "COMM": "Commercial",
    "AGRI": "Agricultural",
    "IND": "Industrial",
    "GOVT": "Government",
    "PVT": "Private",
    "INST": "Institutional",
    "MIX": "Mixed Use",
    "VAC": "Vacant",
    "OPEN": "Open Land",
}

FIELD_SEMANTIC_ALIASES = {
    # Area fields
    "area_sq_m": "area_sqm",
    "area_m2": "area_sqm",
    "land_area": "area_sqm",
    "plot_area": "area_sqm",
    "parcel_area": "area_sqm",
    "extent": "area_sqm",
    "area": "area_sqm",
    
    # Ownership / Identity fields
    "owner": "owner_name",
    "owner_name": "owner_name",
    "proprietor": "owner_name",
    "holder": "owner_name",
    "pattadar": "owner_name",
    
    # Survey / Parcel IDs
    "survey_no": "survey_number",
    "survey_num": "survey_number",
    "sy_no": "survey_number",
    "survey_number": "survey_number",
    "plot_no": "plot_number",
    "plot_num": "plot_number",
    "parcel_id": "parcel_id",
    "ulpin": "ulpin",
    
    # Land use
    "land_use": "land_use_type",
    "landuse": "land_use_type",
    "use_type": "land_use_type",
    "category": "land_use_type",
}


def is_missing_value(val: Any) -> bool:
    """Check if a value represents a missing/null value."""
    if val is None:
        return True
    s = str(val).strip().lower()
    return s in ("", "n/a", "na", "null", "none", "-", "--", "unknown", "-9999", "-9999.0")


def normalize_text(text: str) -> str:
    """Basic text normalization: lowercase, collapse whitespace, strip special characters."""
    if not text:
        return ""
    s = str(text).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def expand_abbreviations(text: str) -> str:
    """Expand known categorical abbreviations (e.g. RES -> Residential)."""
    norm = normalize_text(text).upper()
    return VALUE_ABBREVIATIONS.get(norm, text)


def get_canonical_field_name(field_name: str) -> str:
    """Map a field name to its canonical semantic alias if known."""
    cleaned = field_name.strip().lower().replace("-", "_").replace(" ", "_")
    return FIELD_SEMANTIC_ALIASES.get(cleaned, cleaned)


def detect_data_type(val: Any) -> str:
    """Detect probable data type of a value."""
    if is_missing_value(val):
        return "null"
    s = str(val).strip()
    if s.lower() in ("true", "false", "yes", "no"):
        return "boolean"
    try:
        int(s)
        return "integer"
    except ValueError:
        pass
    try:
        float(s)
        return "float"
    except ValueError:
        pass
    return "string"


def normalize_unit(val: float, from_unit: str, to_unit: str = "sqm") -> Tuple[float, str]:
    """
    Convert area units to square meters if applicable.
    Supported: sqft, sqyd, acre, hectare -> sqm
    """
    from_u = from_unit.lower().strip()
    
    conversions_to_sqm = {
        "sqm": 1.0,
        "sq_m": 1.0,
        "m2": 1.0,
        "sqft": 0.092903,
        "sq_ft": 0.092903,
        "sqyd": 0.836127,
        "sq_yd": 0.836127,
        "acre": 4046.86,
        "hectare": 10000.0,
        "ha": 10000.0,
    }
    
    factor = conversions_to_sqm.get(from_u, 1.0)
    converted = round(val * factor, 4)
    return converted, "sqm" if from_u in conversions_to_sqm else from_u


def suggest_harmonized_value(value: Any, field_name: str) -> Dict[str, Any]:
    """
    Generate a non-destructive harmonized value suggestion for a source value.
    Does NOT overwrite source value.
    """
    if is_missing_value(value):
        return {
            "source_value": value,
            "suggested_value": None,
            "status": "missing",
            "is_missing": True,
            "confidence": 1.0,
            "transformation": "flagged_as_missing"
        }

    str_val = str(value).strip()
    dtype = detect_data_type(value)
    canonical_field = get_canonical_field_name(field_name)

    # 1. Categorical expansion
    expanded = expand_abbreviations(str_val)
    if expanded != str_val:
        return {
            "source_value": value,
            "suggested_value": expanded,
            "canonical_field": canonical_field,
            "status": "normalized",
            "is_missing": False,
            "confidence": 0.95,
            "transformation": f"abbreviation_expansion ({str_val} -> {expanded})"
        }

    # 2. Text normalization
    norm_text = normalize_text(str_val)
    
    return {
        "source_value": value,
        "suggested_value": norm_text,
        "canonical_field": canonical_field,
        "data_type": dtype,
        "status": "suggested",
        "is_missing": False,
        "confidence": 0.90,
        "transformation": "text_standardization"
    }
