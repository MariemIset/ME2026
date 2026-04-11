# Project Documentation: Airline Loyalty Data Warehouse (Normalized Architecture)

## 1. Executive Summary
This project transforms raw, disconnected CSV files containing airline customer data into a centralized, production-grade Data Warehouse built in PostgreSQL. Moving beyond a basic flat structure, this warehouse utilizes a normalized 3rd Normal Form (3NF) / Snowflake Star Schema. The primary goal of this architecture is to provide a highly efficient, scalable "Single Source of Truth" that is perfectly cleaned, structured, and feature-engineered to feed downstream Machine Learning (ML) models and Business Intelligence (BI) dashboards.

## 2. Business Objectives (The "Why")
Every technical decision and feature engineered in this Data Warehouse was made to support the following Business Objectives (BOs):
* **BO 1: Predictive Churn Modeling:** Identify which active loyalty members are at risk of canceling their memberships by analyzing behavioral shifts.
* **BO 2: Points Program Optimization:** Analyze how efficiently customers earn and burn points across different marketing promotions to ensure the loyalty program remains profitable.
* **BO 3: Satisfaction Driver Analysis:** Pinpoint exactly which operational metrics (e.g., flight delays, legroom) have the highest mathematical impact on overall passenger satisfaction.

## 3. Data Architecture & Relationships
To ensure data integrity, eliminate redundancy, and optimize for advanced querying, the warehouse isolates descriptive attributes into dedicated Dimensions, linked via Foreign Keys to measurable Facts.

### The Dimensions (Context)
* **`dim_geography`:** A normalized lookup table storing unique location data to prevent repeating massive string values.
    * *Primary Key:* `location_id`
* **`dim_promotion`:** A lookup table isolating marketing enrollment campaigns. 
    * *Primary Key:* `promotion_id`
* **`dim_customer`:** A lean profile table storing static demographic data (age, salary, etc.). Text-heavy geographic and promotional data have been replaced with integer Foreign Keys.
    * *Primary Key:* `loyalty_number`
    * *Foreign Keys:* `location_id`, `promotion_id`
* **`dim_calendar`:** A standard time-tracking table used to group data by year, quarter, or month.
    * *Primary Key:* `date_key`

### The Facts (Events)
* **`fact_flight_activity`:** Stores the monthly transactional behavior of our customers. 
    * *Foreign Keys:* Connects to `dim_customer` via `loyalty_number` and `dim_calendar` via `date_key` (which was programmatically engineered from separate year/month columns).
* **`fact_satisfaction_survey`:** Stores individual survey results regarding the in-flight and airport experience. This acts as a standalone dataset for generalized sentiment analysis.

## 4. The ETL Pipeline (Extract, Transform, Load)
Data is processed using a modular Python orchestrator built with the `pandas` and `sqlalchemy` libraries. The pipeline extracts raw CSVs, normalizes the data dynamically, engineers features, and loads it into PostgreSQL.

* **`load_dim_customer()`**
    * *Action:* Extracts distinct locations and promotions from the raw customer file, auto-generates sequential IDs, pushes these to `dim_geography` and `dim_promotion`, and maps the IDs back to the main customer dataframe before loading `dim_customer`.
    * *Purpose:* Enforces database normalization and dramatically reduces storage footprint.
* **`load_dim_calendar()`**
    * *Action:* Converts flat text strings into explicit `datetime` objects.
* **`load_fact_flight_activity()`**
    * *Action:* Maps raw headers to the schema, standardizes the `date_key` for seamless cross-platform BI joins, and performs critical **Feature Engineering**.
    * *Purpose:* Calculates ML-ready columns like `avg_distance_per_flight` and `points_per_flight`. This directly supports **BO 1** and **BO 2** by providing models with behavioral indicators (e.g., flagging that churned customers only fly an average of 203 km per flight).
* **`load_fact_satisfaction_survey()`**
    * *Action:* Uses a hardcoded mapping dictionary to clean long, messy survey questions (e.g., "Departure and Arrival Time Convenience" becomes `convenience_score`).
    * *Purpose:* Direct support for **BO 3**, converting text into a clean matrix of numerical scores required by classification algorithms.
