from typing import List, Tuple

from rapidfuzz import fuzz, process


def best_match(candidate: str, choices: List[str], threshold: float = 0.82) -> Tuple[str, float]:
    """Return the best fuzzy match and score in [0,1] using ratio/100.
    If no match >= threshold, returns ("", 0.0).
    """
    try:
        if not candidate or not choices:
            return "", 0.0
        res = process.extractOne(candidate, choices, scorer=fuzz.ratio)
        if not res:
            return "", 0.0
        choice, score, _ = res
        norm = float(score) / 100.0
        if norm >= threshold:
            return choice, norm
        return "", 0.0
    except Exception:
        return "", 0.0
