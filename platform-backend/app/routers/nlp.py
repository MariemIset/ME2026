from fastapi import APIRouter, Query
from sqlalchemy import text
from app.database import engine

router = APIRouter(tags=["NLP"])


@router.get("/api/nlp/sentiment-timeline")
def get_sentiment_timeline(days: int = 30):
    query = text("""
        SELECT
            s.overall_satisfaction,
            COUNT(*) as cnt
        FROM fact_satisfaction_survey s
        GROUP BY s.overall_satisfaction
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).all()

    positive = 0
    negative = 0
    for r in rows:
        if r[0] == "Satisfied":
            positive = r[1]
        else:
            negative = r[1]

    total = positive + negative
    pos_pct = round(positive / total * 100, 2) if total > 0 else 50
    neg_pct = round(negative / total * 100, 2) if total > 0 else 50

    return {
        "totalComments": int(total),
        "positivePercent": pos_pct,
        "negativePercent": neg_pct,
        "timeline": [
            {"name": "Positive", "value": pos_pct},
            {"name": "Negative", "value": neg_pct}
        ]
    }


@router.get("/api/nlp/themes")
def get_themes():
    query = text("""
        SELECT comment_text
        FROM fact_satisfaction_survey
        WHERE comment_text IS NOT NULL AND btrim(comment_text) != ''
        LIMIT 100
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).scalars().all()

    word_freq = {}
    for comment in rows:
        for word in comment.lower().split():
            word = word.strip(".,!?\"';:()[]")
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "keywords": [{"word": w, "count": c} for w, c in sorted_words]
    }