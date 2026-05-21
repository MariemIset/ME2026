-- =========================================================================
-- BO2 / M2 — Redemption outcome window
--
-- For each customer, did they redeem any points in
--   (:as_of_date, :outcome_end_date]?
--
-- Returned as a long table summarising the outcome window. Python attaches
-- it to the customer base and constructs the binary label.
-- =========================================================================

SELECT
    f.loyalty_number,
    SUM(f.points_redeemed)            AS outcome_points_redeemed,
    SUM(f.dollar_cost_points_redeemed) AS outcome_redemption_dollars,
    SUM(f.total_flights)              AS outcome_total_flights
FROM fact_flight_activity f
WHERE f.date_key >  :as_of_date
  AND f.date_key <= :outcome_end_date
GROUP BY f.loyalty_number;
