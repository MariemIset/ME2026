-- =========================================================================
-- BO1 — Flight activity in the observation window
--
-- Pulls activity strictly BEFORE :as_of_date and on/after
-- :window_start_date. The Python layer computes :window_start_date as
--   as_of_date - observation_months months
-- to keep the SQL portable and free of dialect-specific casting tricks.
--
-- Bindings:
--   :as_of_date           — snapshot cutoff (DATE)
--   :window_start_date    — earliest date_key to include (DATE)
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
