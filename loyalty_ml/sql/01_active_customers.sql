-- =========================================================================
-- BO2 — Active customer base at :as_of_date
--
-- Eligible for loyalty optimization (M1, M2, M3 scoring populations):
--   * Enrolled on or before :as_of_date
--   * Not cancelled by :as_of_date (churned customers are out of scope)
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
    p.enrollment_type
FROM dim_customer c
LEFT JOIN dim_geography g ON g.location_id  = c.location_id
LEFT JOIN dim_promotion p ON p.promotion_id = c.promotion_id
WHERE MAKE_DATE(c.enrollment_year,
                COALESCE(c.enrollment_month, 1), 1) <= :as_of_date
  AND (
        c.cancellation_year IS NULL
        OR MAKE_DATE(c.cancellation_year,
                     COALESCE(c.cancellation_month, 12), 1) > :as_of_date
      );
