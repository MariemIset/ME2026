-- =========================================================================
-- BO2 — Flight + points activity in the OBSERVATION window
-- Feeds M1 (segmentation) and M2 (redemption prediction) features.
-- Window is strictly < :as_of_date and >= :window_start_date (computed in Python).
-- =========================================================================

SELECT
    f.loyalty_number,
    f.activity_year,
    f.activity_month,
    f.date_key,
    f.total_flights,
    f.distance,
    f.points_accumulated,
    f.points_redeemed,
    f.dollar_cost_points_redeemed,
    f.cost_per_point,
    f.avg_distance_per_flight,
    f.points_per_flight,
    f.is_redemption_month
FROM fact_flight_activity f
WHERE f.date_key <  :as_of_date
  AND f.date_key >= :window_start_date
ORDER BY f.loyalty_number, f.date_key;
