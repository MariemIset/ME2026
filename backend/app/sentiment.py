from __future__ import annotations

import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Short social text; strong on slang vs lexicon-only models
MODEL_NAME = os.environ.get(
    "SENTIMENT_MODEL",
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
)

_tokenizer: AutoTokenizer | None = None
_model: AutoModelForSequenceClassification | None = None


def initialize_model() -> None:
    """Load tokenizer + model once (CPU). Call from FastAPI lifespan before any analyze_text."""
    global _tokenizer, _model
    if _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    _model.eval()


def _ensure_loaded() -> None:
    if _model is None or _tokenizer is None:
        initialize_model()


def _alias_to_canonical(raw: str) -> str | None:
    x = (raw or "").strip().lower()
    if x in ("positive", "pos", "label_pos"):
        return "positive"
    if x in ("negative", "neg", "label_neg"):
        return "negative"
    if x in ("neutral", "neu", "label_neu"):
        return "neutral"
    return None


def _collapse_probs(raw: dict[str, float]) -> dict[str, float]:
    out = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    for lab, pr in raw.items():
        c = _alias_to_canonical(lab)
        if c is not None:
            out[c] += float(pr)
    return out


def analyze_text(text: str) -> tuple[str, float]:
    """
    Return (sentiment_label, polarity).

    sentiment: positive | negative | neutral from model argmax.
    polarity: P(positive) - P(negative) in [-1, 1] (neutral mass lowers magnitude).
    """
    _ensure_loaded()
    assert _model is not None and _tokenizer is not None

    t = (text or "").strip()
    if not t:
        return "neutral", 0.0

    inputs = _tokenizer(
        t,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=False,
    )
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]

    id2label = _model.config.id2label
    n = probs.shape[0]
    labels: list[str] = []
    for i in range(n):
        raw = id2label.get(i) if hasattr(id2label, "get") else id2label[i]
        if raw is None and hasattr(id2label, "get"):
            raw = id2label.get(str(i))
        labels.append(str(raw).lower())

    raw_p = {labels[i]: float(probs[i]) for i in range(len(labels))}
    p = _collapse_probs(raw_p)

    sentiment = max(p, key=p.get)
    polarity = p["positive"] - p["negative"]
    polarity = max(-1.0, min(1.0, polarity))

    return sentiment, polarity
