from contextlib import asynccontextmanager
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.sentiment import analyze_text, initialize_model
from app.themes import bigram_counts, complaint_topic_counts, keyword_counts

DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password123")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "data_warehouse")
DB_TABLE = os.environ.get("DB_TABLE", "fact_satisfaction_survey")
DB_COMMENT_COLUMN = os.environ.get("DB_COMMENT_COLUMN", "comment_text")
SEED_LIMIT = int(os.environ.get("SEED_LIMIT", "5000"))


def _database_url() -> str:
    override = os.environ.get("DATABASE_URL")
    if override:
        return override
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def _safe_identifier(value: str, default: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""):
        return value
    return default


def _load_seed_reviews() -> list[dict]:
    """
    Load startup reviews from PostgreSQL comments table.
    Returns rows in the shape consumed by Analyze page sample format:
    [{"review": "...", "date": None}, ...]
    """
    engine = create_engine(_database_url())
    table_name = _safe_identifier(DB_TABLE, "fact_satisfaction_survey")
    comment_col = _safe_identifier(DB_COMMENT_COLUMN, "comment_text")
    sql = text(
        f"""
        SELECT {comment_col} AS review
        FROM {table_name}
        WHERE {comment_col} IS NOT NULL
          AND btrim({comment_col}) <> ''
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": SEED_LIMIT}).mappings().all()
    return [{"review": r["review"], "date": None} for r in rows]


class ReviewItem(BaseModel):
    review: str = Field(..., min_length=1)
    date: str | None = None


class AnalyzeRequest(BaseModel):
    reviews: list[ReviewItem] = Field(..., min_length=1)


class StoredReview(BaseModel):
    review: str
    date: str | None
    sentiment: str
    polarity: float


# In-memory store: seeded from PostgreSQL on startup
_history: list[StoredReview] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_model()
    try:
        sample = _load_seed_reviews()
        for row in sample:
            s, p = analyze_text(row["review"])
            _history.append(
                StoredReview(
                    review=row["review"],
                    date=row.get("date"),
                    sentiment=s,
                    polarity=p,
                )
            )
        print(f"Seeded {len(_history)} reviews from PostgreSQL.")
    except Exception as e:
        print(f"Could not seed reviews from PostgreSQL: {e}")
    yield


app = FastAPI(title="Review Sentiment API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sample-reviews")
def sample_reviews():
    return _load_seed_reviews()


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    global _history
    results: list[dict] = []
    batch: list[StoredReview] = []

    for item in req.reviews:
        text = item.review.strip()
        if not text:
            continue
        sentiment, polarity = analyze_text(text)
        row = StoredReview(
            review=text,
            date=item.date,
            sentiment=sentiment,
            polarity=polarity,
        )
        batch.append(row)
        results.append(
            {
                "review": text,
                "date": item.date,
                "sentiment": sentiment,
                "polarity": round(polarity, 4),
            }
        )

    if not results:
        raise HTTPException(status_code=400, detail="No non-empty reviews to analyze.")

    _history.extend(batch)
    return {"results": results, "count": len(results)}


@app.get("/trends")
def trends():
    if not _history:
        return {
            "by_date": [],
            "totals": {"positive": 0, "negative": 0, "neutral": 0},
        }

    by_date: dict[str, dict[str, int]] = {}
    totals = {"positive": 0, "negative": 0, "neutral": 0}

    for r in _history:
        totals[r.sentiment] = totals.get(r.sentiment, 0) + 1
        key = r.date or "unknown"
        bucket = by_date.setdefault(key, {"positive": 0, "negative": 0, "neutral": 0})
        bucket[r.sentiment] = bucket.get(r.sentiment, 0) + 1

    series = [
        {
            "date": d,
            "positive": v.get("positive", 0),
            "negative": v.get("negative", 0),
            "neutral": v.get("neutral", 0),
        }
        for d, v in sorted(by_date.items(), key=lambda x: x[0])
    ]

    return {"by_date": series, "totals": totals}


@app.get("/themes")
def themes(top_keywords: int = 12, top_phrases: int = 10):
    texts = [r.review for r in _history]

    if not texts:
        sample = _load_seed_reviews()
        texts = [r["review"] for r in sample]

    if not texts:
        return {"keywords": [], "phrases": [], "complaint_topics": []}

    return {
        "keywords": keyword_counts(texts, top_k=top_keywords),
        "phrases": bigram_counts(texts, top_k=top_phrases),
        "complaint_topics": complaint_topic_counts(texts),
    }
