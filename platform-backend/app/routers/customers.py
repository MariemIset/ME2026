from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine

router = APIRouter(tags=["Customers"])


@router.get("/api/customers/random-sample")
def get_random_customer_sample():
    query = text("""
        SELECT
            c.loyalty_number,
            c.loyalty_card,
            g.city,
            g.province,
            c.clv,
            p.enrollment_type,
            c.cancellation_year
        FROM dim_customer c
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        LEFT JOIN dim_promotion p ON c.promotion_id = p.promotion_id
        ORDER BY RANDOM()
        LIMIT 50
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    return [
        {
            "loyaltyNumber": int(r["loyalty_number"]),
            "loyaltyCard": r["loyalty_card"],
            "city": r["city"] or "",
            "province": r["province"] or "",
            "clv": round(float(r["clv"]), 2) if r["clv"] else 0,
            "enrollmentType": r["enrollment_type"] or "",
            "isChurned": r["cancellation_year"] is not None,
        }
        for r in rows
    ]
