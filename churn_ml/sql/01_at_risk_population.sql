-- =========================================================================
-- BO1 — At-risk customer snapshot at :as_of_date
--
-- A customer is "at risk" of churn at the cutoff if:
--   * They were enrolled on or before :as_of_date
--   * They had NOT cancelled by :as_of_date
--
-- Output: one row per loyalty_number with frozen demographic / contextual
-- attributes plus a cancellation_date (NULL if still active).
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
              COALESCE(c.enrollment_month, 1),
              1)                                           AS enrollment_date,
    CASE
        WHEN c.cancellation_year IS NOT NULL
        THEN MAKE_DATE(c.cancellation_year,
                       COALESCE(c.cancellation_month, 12),
                       1)
    END                                                    AS cancellation_date,
    g.country,
    g.province,
    g.city,
    p.enrollment_type
FROM dim_customer c
LEFT JOIN dim_geography g ON g.location_id  = c.location_id
LEFT JOIN dim_promotion p ON p.promotion_id = c.promotion_id
WHERE MAKE_DATE(c.enrollment_year,
                COALESCE(c.enrollment_month, 1),
                1) <= :as_of_date
  AND (
        c.cancellation_year IS NULL
        OR MAKE_DATE(c.cancellation_year,
                     COALESCE(c.cancellation_month, 12),
                     1) > :as_of_date
      );
