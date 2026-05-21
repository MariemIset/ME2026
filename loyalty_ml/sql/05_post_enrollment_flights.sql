-- =========================================================================
-- BO2 / M3 — Post-enrollment flight panel (for uplift outcome construction)
--
-- We pull all flight activity rows; Python filters to the
-- 6-month post-enrollment window per customer.
-- =========================================================================

SELECT
    f.loyalty_number,
    f.date_key,
    f.total_flights
FROM fact_flight_activity f;
