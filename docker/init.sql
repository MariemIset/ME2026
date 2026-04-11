-- 1. DROP EXISTING TABLES
DROP TABLE IF EXISTS fact_flight_activity;
DROP TABLE IF EXISTS fact_satisfaction_survey;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_calendar;
DROP TABLE IF EXISTS dim_geography;
DROP TABLE IF EXISTS dim_promotion;

-- 2. CREATE NORMALIZED DIMENSIONS
CREATE TABLE dim_calendar (
    date_key DATE PRIMARY KEY,
    start_of_year DATE,
    start_of_quarter DATE,
    start_of_month DATE
);

CREATE TABLE dim_geography (
    location_id SERIAL PRIMARY KEY, -- Auto-increments
    country VARCHAR(50),
    province VARCHAR(50),
    city VARCHAR(50),
    postal_code VARCHAR(20)
);

CREATE TABLE dim_promotion (
    promotion_id SERIAL PRIMARY KEY,
    enrollment_type VARCHAR(50)
);

-- 3. CREATE THE LEAN CUSTOMER DIMENSION
CREATE TABLE dim_customer (
    loyalty_number INT PRIMARY KEY,
    location_id INT REFERENCES dim_geography(location_id),
    promotion_id INT REFERENCES dim_promotion(promotion_id),
    gender VARCHAR(10),
    education VARCHAR(50),
    salary NUMERIC(10,2),
    marital_status VARCHAR(20),
    loyalty_card VARCHAR(20),
    clv NUMERIC(10,2),
    enrollment_year INT,
    enrollment_month INT,
    cancellation_year INT,
    cancellation_month INT
);

-- 4. CREATE FACT TABLES (With our ML engineered features included)
CREATE TABLE fact_flight_activity (
    activity_id SERIAL PRIMARY KEY,
    loyalty_number INT REFERENCES dim_customer(loyalty_number),
    activity_year INT,
    activity_month INT,
    total_flights INT,
    distance INT,
    points_accumulated INT,
    points_redeemed INT,
    date_key DATE,
    dollar_cost_points_redeemed NUMERIC(10,2),
    cost_per_point NUMERIC(10,4),
    avg_distance_per_flight NUMERIC(10,2),
    points_per_flight NUMERIC(10,2),
    is_redemption_month INT
);

CREATE TABLE fact_satisfaction_survey (
    survey_id INT PRIMARY KEY,
    gender VARCHAR(10),
    age INT,
    customer_type VARCHAR(50),
    type_of_travel VARCHAR(50),
    flight_class VARCHAR(50),
    flight_distance INT,
    departure_delay_min INT,
    arrival_delay_min INT,
    convenience_score INT,
    online_booking_score INT,
    check_in_score INT,
    online_boarding_score INT,
    gate_location_score INT,
    on_board_service_score INT,
    seat_comfort_score INT,
    leg_room_score INT,
    cleanliness_score INT,
    food_drink_score INT,
    in_flight_service_score INT,
    wifi_score INT,
    entertainment_score INT,
    baggage_handling_score INT,
    overall_satisfaction VARCHAR(50)
);