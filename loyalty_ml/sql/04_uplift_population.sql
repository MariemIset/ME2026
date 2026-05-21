-- =========================================================================
-- BO2 / M3 — Uplift modeling population (pre-treatment features + outcome)
--
-- Treatment (T):  enrollment_type = '2018 Promotion'   → 1
-- Outcome  (Y):   ≥ 1 flight in the 6 months following enrollment_date
--                 (computed in Python from the activity panel)
-- Features:       pre-treatment demographics only (no leakage)
--
-- We pull every customer (regardless of cancellation status) because the
-- uplift question is "would marketing-driven enrollment cause activation?".
-- Filters and outcome construction happen on the Python side.
-- =========================================================================

SELECT
    c.loyalty_number,
    c.gender,
    c.education,
    c.salary,
    c.marital_status,
    c.loyalty_card,
    c.clv,
    c.enrollment_year,
    c.enrollment_month,
    MAKE_DATE(c.enrollment_year,
              COALESCE(c.enrollment_month, 1), 1)          AS enrollment_date,
    g.country,
    g.province,
    g.city,
    p.enrollment_type,
    CASE WHEN p.enrollment_type = '2018 Promotion' THEN 1 ELSE 0 END AS treatment
FROM dim_customer c
LEFT JOIN dim_geography g ON g.location_id  = c.location_id
LEFT JOIN dim_promotion p ON p.promotion_id = c.promotion_id;
