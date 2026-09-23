"""Conservative text normalization and similarity matching."""
import re
from difflib import SequenceMatcher


STOPWORDS = {"и", "или", "в", "на", "по", "для", "с", "к", "из", "от", "а", "о", "the", "and"}


def normalize(text: str) -> set[str]:
    words = re.findall(r"[\w-]+", text.lower().replace("ё", "е"), flags=re.UNICODE)
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def similarity(left: str, right: str) -> float:
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    jaccard = len(a & b) / len(a | b)
    sequence = SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return max(jaccard, sequence * 0.75)


def best_match(text: str, candidates: list[str]) -> tuple[int | None, float]:
    scored = [(similarity(text, item), idx) for idx, item in enumerate(candidates)]
    if not scored:
        return None, 0.0
    score, idx = max(scored)
    return (idx, score) if score >= 0.45 else (None, score)
