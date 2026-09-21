def classify_confidence(score: float) -> str:
    """
    Convert a numeric confidence score
    into a human-readable confidence level.
    """

    score = float(score or 0.0)

    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "medium"

    return "low"


def build_confidence_result(score: float) -> dict:
    """
    Return both the numeric score and
    its confidence classification.
    """

    score = round(
        max(0.0, min(1.0, float(score or 0.0))),
        4
    )

    return {
        "confidence_score": score,
        "confidence_level": classify_confidence(score)
    }