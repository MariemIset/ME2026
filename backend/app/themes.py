import re
from collections import Counter
from typing import Pattern

_TOKEN = re.compile(r"[a-z0-9']+", re.I)

# Precompiled regexes: a comment matches a topic if any pattern matches (multi-topic allowed).
_COMPLAINT_TOPIC_SPECS: list[tuple[str, str, list[str]]] = [
    (
        "delays",
        "Delays & lateness",
        [
            r"\bdelay",
            r"\bdelayed\b",
            r"\blate\b",
            r"\btarmac\b",
            r"\brunway\b",
            r"hours?\s+late",
            r"sitting on (the )?(plane|runway|tarmac)",
            r"held (on|at)",
        ],
    ),
    (
        "cancellations",
        "Cancellations & rebooking",
        [
            r"\bcancel",
            r"\bcancelled\b",
            r"\bcanceled\b",
            r"\breschedul",
            r"\bbumped\b",
            r"\bno show\b",
            r"missed (my )?connection",
        ],
    ),
    (
        "cleanliness",
        "Cleanliness & cabin condition",
        [
            r"\bdirty\b",
            r"\bfilthy\b",
            r"\bgross\b",
            r"\bsmell",
            r"\bstink",
            r"\bunclean\b",
            r"\bmessy\b",
            r"cleanliness",
            r"disgusting",
        ],
    ),
    (
        "luggage",
        "Luggage & baggage",
        [
            r"\bluggage\b",
            r"\bbaggage\b",
            r"lost bag",
            r"\bsuitcase\b",
            r"checked bag",
            r"mishandled",
            r"never arrived",
            r"damaged bag",
        ],
    ),
    (
        "staff_service",
        "Staff & service",
        [
            r"\brude\b",
            r"\bunhelpful\b",
            r"\bignored\b",
            r"\bcrew\b",
            r"\battendant\b",
            r"\bsteward",
            r"poor service",
            r"bad service",
            r"customer service",
        ],
    ),
    (
        "booking_boarding",
        "Booking & boarding",
        [
            r"\bbooking\b",
            r"check[\s-]?in",
            r"\bboarding\b",
            r"\bkiosk\b",
            r"boarding pass",
            r"upgrade",
            r"overbook",
        ],
    ),
    (
        "fees_refunds",
        "Fees, refunds & compensation",
        [
            r"\brefund\b",
            r"\bfee\b",
            r"\bfees\b",
            r"\bcharge\b",
            r"\bexpensive\b",
            r"\bcompensation\b",
            r"\bvoucher\b",
            r"\bmiles\b",
        ],
    ),
    (
        "seat_comfort",
        "Seats & comfort",
        [
            r"\bseat\b",
            r"\bcramped\b",
            r"\blegroom\b",
            r"\bleg room\b",
            r"\brecline\b",
            r"\buncomfortable\b",
            r"tight spacing",
        ],
    ),
    (
        "food_drinks",
        "Food & drinks",
        [
            r"\bfood\b",
            r"\bmeal\b",
            r"\bsnack\b",
            r"\bdrink\b",
            r"\bcatering\b",
            r"\bhungry\b",
            r"no food",
        ],
    ),
    (
        "wifi_entertainment",
        "Wi‑Fi & entertainment",
        [
            r"\bwifi\b",
            r"wi-?fi",
            r"\bentertainment\b",
            r"\bscreen\b",
            r"in-?flight entertainment",
            r"\bmovie\b",
        ],
    ),
]

_COMPILED_TOPICS: list[tuple[str, str, list[Pattern[str]]]] = [
    (key, label, [re.compile(p, re.I | re.MULTILINE) for p in pats])
    for key, label, pats in _COMPLAINT_TOPIC_SPECS
]


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if len(t) > 2]


STOP = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her",
    "was", "one", "our", "out", "has", "have", "been", "were", "they", "this",
    "that", "with", "from", "your", "what", "when", "who", "how", "its", "it's",
    "too", "also", "just", "very", "more", "some", "than", "then", "them", "will",
    "into", "about", "there", "here", "would", "could", "should", "only", "really",
    "much", "such", "any", "get", "got", "did", "does", "doing", "done", "like",
}


def keyword_counts(reviews: list[str], top_k: int = 15) -> list[dict]:
    counts: Counter[str] = Counter()
    for r in reviews:
        for w in _tokens(r):
            if w in STOP:
                continue
            counts[w] += 1
    return [{"word": w, "count": c} for w, c in counts.most_common(top_k)]


def bigram_counts(reviews: list[str], top_k: int = 10) -> list[dict]:
    """Simple frequent two-word phrases (lightweight alternative to vectorizers)."""
    counts: Counter[str] = Counter()
    for r in reviews:
        words = [w for w in _tokens(r) if w not in STOP]
        for a, b in zip(words, words[1:]):
            counts[f"{a} {b}"] += 1
    return [{"phrase": p, "count": c} for p, c in counts.most_common(top_k)]


def complaint_topic_counts(reviews: list[str]) -> list[dict]:
    """
    Count how many comments mention each complaint theme (keyword/regex match).
    One comment can increment multiple topics.
    """
    rows: list[dict] = []
    for key, label, patterns in _COMPILED_TOPICS:
        n = 0
        for raw in reviews:
            text = (raw or "").strip()
            if not text:
                continue
            lowered = text.lower()
            if any(p.search(lowered) for p in patterns):
                n += 1
        rows.append({"topic_key": key, "topic": label, "count": n})
    rows.sort(key=lambda r: (-r["count"], r["topic"]))
    return rows
