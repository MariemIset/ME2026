SELECT
    c.loyalty_card as "VIP Tier",
    COUNT(DISTINCT c.loyalty_number) as "Total Customers",
    ROUND(AVG(f.cost_per_point), 4) as "Average Cost per Point ($)",
    SUM(f.points_redeemed) as "Total Points Redeemed"
FROM dim_customer c
JOIN fact_flight_activity f ON c.loyalty_number = f.loyalty_number
WHERE f.cost_per_point > 0 -- Only calculate based on actual redemptions
GROUP BY c.loyalty_card
ORDER BY "Average Cost per Point ($)" DESC;
#---------------
SELECT
    c.marital_status as "Marital Status",
    p.enrollment_type as "Enrollment Promotion", -- Now coming from dim_promotion
    ROUND(AVG(f.points_per_flight), 2) as "Avg Points Earned Per Flight"
FROM fact_flight_activity f
JOIN dim_customer c ON f.loyalty_number = c.loyalty_number
JOIN dim_promotion p ON c.promotion_id = p.promotion_id -- The new hop!
WHERE f.total_flights > 0
GROUP BY c.marital_status, p.enrollment_type
ORDER BY "Avg Points Earned Per Flight" DESC;
#----------------
SELECT
    CASE WHEN c.cancellation_year IS NOT NULL THEN 'Canceled (Churned)'
         ELSE 'Active Member' END as "Membership Status",
    ROUND(AVG(f.avg_distance_per_flight), 2) as "Typical Flight Distance (km)",
    ROUND(AVG(f.total_flights), 2) as "Average Flights per Month"
FROM dim_customer c
JOIN fact_flight_activity f ON c.loyalty_number = f.loyalty_number
GROUP BY
    CASE WHEN c.cancellation_year IS NOT NULL THEN 'Canceled (Churned)'
         ELSE 'Active Member' END;