from fastapi import APIRouter, Query
from sqlalchemy import text
from app.database import engine

router = APIRouter(tags=["KPIs"])


def clean_filter_params(loyalty_cards: str | None, provinces: str | None):
    cards_list = [c.strip() for c in loyalty_cards.split(",")] if loyalty_cards else []
    provs_list = [p.strip() for p in provinces.split(",")] if provinces else []
    return cards_list, provs_list


def get_filter_sql_and_params(cards: list[str], provs: list[str]):
    clauses = []
    params = {}
    if cards:
        clauses.append("c.loyalty_card IN :cards")
        params["cards"] = tuple(cards)
    if provs:
        clauses.append("g.province IN :provs")
        params["provs"] = tuple(provs)
    filter_sql = ""
    if clauses:
        filter_sql = " AND " + " AND ".join(clauses)
    return filter_sql, params


@router.get("/api/kpis")
def get_kpis(loyalty_cards: str | None = None, provinces: str | None = None):
    cards, provs = clean_filter_params(loyalty_cards, provinces)
    filter_sql, params = get_filter_sql_and_params(cards, provs)

    cust_query = text(f"""
        SELECT COUNT(DISTINCT c.loyalty_number) as cnt
        FROM dim_customer c
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        WHERE 1=1 {filter_sql}
    """)
    clv_query = text(f"""
        SELECT AVG(c.clv) as avg_clv
        FROM dim_customer c
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        WHERE 1=1 {filter_sql}
    """)
    churn_query = text(f"""
        SELECT COUNT(*) as churned
        FROM dim_customer c
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        WHERE c.cancellation_year IS NOT NULL {filter_sql}
    """)
    rev_query = text(f"""
        SELECT SUM(f.distance) * 0.08 + SUM(f.points_accumulated) * 0.005 as rev
        FROM fact_flight_activity f
        JOIN dim_customer c ON f.loyalty_number = c.loyalty_number
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        WHERE 1=1 {filter_sql}
    """)

    with engine.connect() as conn:
        total_cust = conn.execute(cust_query, params).scalar() or 0
        avg_clv = conn.execute(clv_query, params).scalar() or 0
        total_churn = conn.execute(churn_query, params).scalar() or 0
        total_rev = conn.execute(rev_query, params).scalar() or 0

    return {
        "totalCustomers": {"value": int(total_cust), "goal": 20000},
        "churnRisk": {"value": int(total_churn), "goal": 1500},
        "avgClv": {"value": round(float(avg_clv), 2), "goal": 8500},
        "totalRevenue": {"value": round(float(total_rev), 2), "goal": 1500000}
    }


@router.get("/api/ceo/revenue-chart")
def get_revenue_chart(loyalty_cards: str | None = None, provinces: str | None = None):
    cards, provs = clean_filter_params(loyalty_cards, provinces)
    filter_sql, params = get_filter_sql_and_params(cards, provs)

    query = text(f"""
        SELECT
            f.activity_month,
            SUM(f.distance) * 0.08 + SUM(f.points_accumulated) * 0.005 as val
        FROM fact_flight_activity f
        JOIN dim_customer c ON f.loyalty_number = c.loyalty_number
        LEFT JOIN dim_geography g ON c.location_id = g.location_id
        WHERE f.activity_year = 2017 AND f.activity_month <= 6 {filter_sql}
        GROUP BY f.activity_month
        ORDER BY f.activity_month
    """)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    with engine.connect() as conn:
        rows = conn.execute(query, params).all()

    result = []
    for r in rows:
        m_idx = int(r[0]) - 1
        m_name = months[m_idx] if 0 <= m_idx < len(months) else f"M{r[0]}"
        result.append({"name": m_name, "value": round(float(r[1]), 2)})

    if not result:
        result = [{"name": months[i], "value": 3000 + i * 500} for i in range(6)]

    return result