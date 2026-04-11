# Project Documentation: Power BI Semantic Layer & Visual Analytics

## 1. Executive Summary
This document outlines the Business Intelligence (BI) architecture built on top of the PostgreSQL Data Warehouse. By importing the normalized PostgreSQL tables into Power BI, we established a robust "Semantic Layer." This layer utilizes Data Analysis Expressions (DAX) to dynamically calculate enterprise-grade metrics and visualizes them across three dedicated dashboards. Each dashboard is strictly aligned with the core Business Objectives (BOs) of the airline's loyalty program.

## 2. The Semantic Data Model
The Power BI data model reflects a strict Snowflake Schema, ensuring high-performance filtering and preventing data duplication. 

* **The Core Star:** `fact_flight_activity` is linked to `dim_customer` (via `loyalty_number`) and `dim_calendar` (via `date_key`) using 1-to-Many relationships.
* **The Snowflake Branches:** `dim_customer` is filtered by `dim_geography` (via `location_id`) and `dim_promotion` (via `promotion_id`) using 1-to-Many relationships.
* **The Standalone Fact:** `fact_satisfaction_survey` remains isolated as it relies on anonymous survey IDs for generalized sentiment analysis.

## 3. DAX Measure Dictionary
To avoid the mathematical pitfalls of averaging averages and to ensure dynamic filtering context, all KPIs are explicitly defined using DAX measures and calculated columns.

### Foundation & Churn Profiling (Supports BO 1)
* **`Churn_Status` (Calculated Column in `dim_customer`):**
    * *Formula:* `IF(ISBLANK('dim_customer'[cancellation_year]), "Active", "Churned")`
    * *Goal:* Creates a definitive text dimension used to color-code visuals and slice dashboards, instantly separating active loyalists from flight risks.
* **`Total Customers` (Measure):**
    * *Formula:* `DISTINCTCOUNT('dim_customer'[loyalty_number])`
    * *Goal:* Provides the baseline denominator for demographic calculations.
* **`Churn Rate %` (Measure):**
    * *Formula:* `DIVIDE(CALCULATE([Total Customers], 'dim_customer'[Churn_Status] = "Churned"), [Total Customers], 0)`
    * *Goal:* Tracks the historical attrition rate of the loyalty program dynamically across any selected geographical or promotional filter.

### Loyalty Program Economics (Supports BO 2)
* **`Total Points Accumulated` & `Total Points Redeemed` (Measures):**
    * *Formula:* `SUM('fact_flight_activity'[points_accumulated])` | `SUM('fact_flight_activity'[points_redeemed])`
    * *Goal:* Calculates the absolute volume of the program's point economy.
* **`Unredeemed Points Liability` (Measure):**
    * *Formula:* `[Total Points Accumulated] - [Total Points Redeemed]`
    * *Goal:* Calculates the financial liability gap. This is critical for the finance department to understand the volume of outstanding points that customers could theoretically cash in at any moment.
* **`Avg Points Per Flight` (Measure):**
    * *Formula:* `DIVIDE(SUM('fact_flight_activity'[points_accumulated]), SUM('fact_flight_activity'[total_flights]), 0)`
    * *Goal:* Calculates true earning efficiency. Using the `DIVIDE(SUM, SUM)` pattern prevents the mathematical error of unequally weighting high-frequency flyers against low-frequency flyers.

### Passenger Satisfaction (Supports BO 3)
* **`Satisfied Passenger %` (Measure):**
    * *Formula:* `DIVIDE(CALCULATE(COUNTROWS('fact_satisfaction_survey'), 'fact_satisfaction_survey'[overall_satisfaction] = "Satisfied"), COUNTROWS('fact_satisfaction_survey'), 0)`
    * *Goal:* Converts raw text survey outputs into a clean, trackable percentage metric for executive reporting.

## 4. Dashboard Architecture
The report is divided into three focused pages, translating the DAX measures into actionable business insights.

### Page 1: Churn Risk & Behavior Profile (BO 1)
* **Objective:** Identify the behavioral traits of customers who leave the airline.
* **Core Visual:** A Scatter Chart plotting `Average Flights` against `Average Distance`, clustered by `Churn_Status`.
* **Business Value:** Visually proves the hypothesis that customers with low flight frequencies and short flight distances hold the highest churn probability.

### Page 2: Program Economics & Promotion ROI (BO 2)
* **Objective:** Monitor financial liabilities and evaluate marketing campaign efficiency.
* **Core Visual 1 (Liability Trend):** A Dual-Axis Line Chart plotting `Total Points Accumulated` against `Total Points Redeemed` over time, exposing the true "earn vs. burn" ratio despite massive scale differences.
* **Core Visual 2 (Promo ROI):** A Bar Chart comparing `Avg Points Per Flight` by `enrollment_type`, immediately highlighting which marketing initiatives yield the highest-value passengers.

### Page 3: Satisfaction Driver Analysis (BO 3)
* **Objective:** Pinpoint the exact operational metrics that damage the customer experience.
* **Core Visual 1 (Pain-Point Heatmap):** A Matrix visual utilizing conditional background formatting to map average component scores (WiFi, Legroom, Check-in) against flight classes, exposing localized service failures.
* **Core Visual 2 (AI Key Influencers):** Leverages Power BI's built-in Machine Learning algorithms to analyze unsummarized row-level data. It mathematically identifies the strongest predictors of a "Dissatisfied" rating (e.g., measuring the exact impact of a 1-point drop in cleanliness on overall satisfaction).