import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os

# 1. Database Connection Setup
DB_USER = 'admin'
DB_PASSWORD = 'password123'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'data_warehouse'

# Create the connection tunnel to PostgreSQL
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# 2. Define File Paths dynamically based on your project layout
# This gets the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate into the Loyalty Program folder
LOYALTY_DIR = os.path.join(BASE_DIR, 'Airline+Loyalty+Program')
CUSTOMER_HISTORY_FILE = os.path.join(LOYALTY_DIR, 'Customer Loyalty History.csv')


def load_dim_customer():
    print("Extracting Customer data...")
    CUSTOMER_HISTORY_FILE = os.path.join(LOYALTY_DIR, 'Customer Loyalty History.csv')
    df_raw = pd.read_csv(CUSTOMER_HISTORY_FILE)

    # Standardize column names
    df_raw.columns = [col.lower().replace(' ', '_') for col in df_raw.columns]

    print("Executing ETL: Normalizing Geography Dimension...")
    # 1. Extract unique locations
    geo_cols = ['country', 'province', 'city', 'postal_code']
    df_geo = df_raw[geo_cols].drop_duplicates().reset_index(drop=True)
    # Generate an ID starting from 1
    df_geo['location_id'] = df_geo.index + 1

    # Push to DB
    df_geo.to_sql('dim_geography', engine, if_exists='append', index=False)
    print("✅ dim_geography loaded.")

    print("Executing ETL: Normalizing Promotion Dimension...")
    # 2. Extract unique promotions
    promo_cols = ['enrollment_type']
    df_promo = df_raw[promo_cols].drop_duplicates().reset_index(drop=True)
    df_promo['promotion_id'] = df_promo.index + 1

    # Push to DB
    df_promo.to_sql('dim_promotion', engine, if_exists='append', index=False)
    print("✅ dim_promotion loaded.")

    print("Executing ETL: Mapping Foreign Keys to Customer Dimension...")
    # 3. Merge the IDs back into the main customer dataframe
    # We join on the text columns to get the IDs, then we drop the text columns
    df_customer = pd.merge(df_raw, df_geo, on=geo_cols, how='left')
    df_customer = pd.merge(df_customer, df_promo, on=promo_cols, how='left')

    # Drop the redundant text columns now that we have location_id and promotion_id
    columns_to_drop = geo_cols + promo_cols
    df_customer = df_customer.drop(columns=columns_to_drop)

    # 4. Final Cleansing (Ensuring correct data types for DB insertion)
    # Pandas sometimes turns ints into floats if there are Nulls. We leave them as floats
    # so SQLAlchemy can safely convert NaN to SQL NULLs.

    print("Loading mapped data into PostgreSQL 'dim_customer' table...")
    df_customer.to_sql('dim_customer', engine, if_exists='append', index=False)
    print("✅ dim_customer loaded securely with Foreign Keys.")
# ----------------------------------------------------------------------

def load_dim_calendar():
    print("Extracting Calendar data...")
    CALENDAR_FILE = os.path.join(LOYALTY_DIR, 'Calendar.csv')

    # Extract
    df_calendar = pd.read_csv(CALENDAR_FILE)

    print("Transforming Calendar data...")
    # Transform 1: Clean column names to match PostgreSQL
    df_calendar.columns = ['date_key', 'start_of_year', 'start_of_quarter', 'start_of_month']

    # Transform 2: Convert text strings to actual Date objects
    # This ensures PostgreSQL recognizes them perfectly as dates, not text
    df_calendar['date_key'] = pd.to_datetime(df_calendar['date_key'])
    df_calendar['start_of_year'] = pd.to_datetime(df_calendar['start_of_year'])
    df_calendar['start_of_quarter'] = pd.to_datetime(df_calendar['start_of_quarter'])
    df_calendar['start_of_month'] = pd.to_datetime(df_calendar['start_of_month'])

    print("Loading data into PostgreSQL 'dim_calendar' table...")
    # Load
    try:
        df_calendar.to_sql('dim_calendar', engine, if_exists='append', index=False)
        print("✅ Successfully loaded dim_calendar!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")



#-----------------------------------------------------
def load_fact_flight_activity():
    print("Extracting Flight Activity data...")
    FLIGHT_FILE = os.path.join(LOYALTY_DIR, 'Customer Flight Activity.csv')
    df_flights = pd.read_csv(FLIGHT_FILE)

    print("Transforming & Engineering Features...")
    # 1. Clean base columns
    df_flights.columns = [col.lower().replace(' ', '_') for col in df_flights.columns]

    df_flights = df_flights.rename(columns={
        'year': 'activity_year',
        'month': 'activity_month'
    })

    # Create a proper date column linking to the 1st of the month
    df_flights['date_key'] = pd.to_datetime(df_flights['activity_year'].astype(str) + '-' +
                                            df_flights['activity_month'].astype(str) + '-01')
    # --------------------

    # 2. FEATURE ENGINEERING
    # Feature 1: Cost per point (Handle div by 0 by checking if points_redeemed > 0)
    df_flights['cost_per_point'] = np.where(df_flights['points_redeemed'] > 0,
                                            df_flights['dollar_cost_points_redeemed'] / df_flights['points_redeemed'],
                                            0.0)

    # Feature 2: Average distance per flight
    df_flights['avg_distance_per_flight'] = np.where(df_flights['total_flights'] > 0,
                                                     df_flights['distance'] / df_flights['total_flights'],
                                                     0.0)

    # Feature 3: Points earned per flight
    df_flights['points_per_flight'] = np.where(df_flights['total_flights'] > 0,
                                               df_flights['points_accumulated'] / df_flights['total_flights'],
                                               0.0)

    # Feature 4: Binary redemption flag (1 if they redeemed, 0 if they didn't)
    df_flights['is_redemption_month'] = np.where(df_flights['points_redeemed'] > 0, 1, 0)

    print("Loading data into PostgreSQL 'fact_flight_activity' table...")
    # Load
    try:
        df_flights.to_sql('fact_flight_activity', engine, if_exists='append', index=False)
        print("✅ Successfully loaded fact_flight_activity with new ML features!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

#---------------------------------------------------
def load_fact_satisfaction_survey():
    print("Extracting Satisfaction Survey data...")
    # Note the different folder path here!
    SURVEY_DIR = os.path.join(BASE_DIR, 'Airline+Passenger+Satisfaction')
    SURVEY_FILE = os.path.join(SURVEY_DIR, 'airline_passenger_satisfaction.csv')

    # Extract
    df_survey = pd.read_csv(SURVEY_FILE)

    print("Transforming Satisfaction Survey data...")

    # 1. Map the raw CSV columns to our clean PostgreSQL schema
    rename_map = {
        'ID': 'survey_id',
        'Gender': 'gender',
        'Age': 'age',
        'Customer Type': 'customer_type',
        'Type of Travel': 'type_of_travel',
        'Class': 'flight_class',
        'Flight Distance': 'flight_distance',
        'Departure Delay': 'departure_delay_min',
        'Arrival Delay': 'arrival_delay_min',
        'Departure and Arrival Time Convenience': 'convenience_score',
        'Ease of Online Booking': 'online_booking_score',
        'Check-in Service': 'check_in_score',
        'Online Boarding': 'online_boarding_score',
        'Gate Location': 'gate_location_score',
        'On-board Service': 'on_board_service_score',
        'Seat Comfort': 'seat_comfort_score',
        'Leg Room Service': 'leg_room_score',
        'Cleanliness': 'cleanliness_score',
        'Food and Drink': 'food_drink_score',
        'In-flight Service': 'in_flight_service_score',
        'In-flight Wifi Service': 'wifi_score',
        'In-flight Entertainment': 'entertainment_score',
        'Baggage Handling': 'baggage_handling_score',
        'Satisfaction': 'overall_satisfaction'
    }

    df_survey = df_survey.rename(columns=rename_map)

    # 2. Data Cleaning Note:
    # Flight datasets almost always have a few blank 'Arrival Delay' rows (e.g., if a flight was canceled or diverted).
    # Pandas will read these as NaN, and SQLAlchemy will load them as NULL.
    # Since we are prepping for ML, we will leave them as NULL in the database,
    # so we can use an imputer in our ML pipeline later to handle them mathematically.

    print("Loading data into PostgreSQL 'fact_satisfaction_survey' table...")
    # Load
    try:
        df_survey.to_sql('fact_satisfaction_survey', engine, if_exists='append', index=False)
        print("Successfully loaded fact_satisfaction_survey!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == '__main__':
     #load_dim_customer()
    #load_dim_calendar()
     load_fact_flight_activity()
    #load_fact_satisfaction_survey()