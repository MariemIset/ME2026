from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from app.database import Base


class DimCalendar(Base):
    __tablename__ = "dim_calendar"
    date_key = Column(Date, primary_key=True)
    start_of_year = Column(Date)
    start_of_quarter = Column(Date)
    start_of_month = Column(Date)


class DimGeography(Base):
    __tablename__ = "dim_geography"
    location_id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(100))
    province = Column(String(100))
    city = Column(String(100))
    postal_code = Column(String(20))


class DimPromotion(Base):
    __tablename__ = "dim_promotion"
    promotion_id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_type = Column(String(50))


class DimCustomer(Base):
    __tablename__ = "dim_customer"
    loyalty_number = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("dim_geography.location_id"))
    promotion_id = Column(Integer, ForeignKey("dim_promotion.promotion_id"))
    gender = Column(String(10))
    education = Column(String(50))
    salary = Column(Float)
    marital_status = Column(String(20))
    loyalty_card = Column(String(50))
    clv = Column(Float)
    enrollment_year = Column(Integer)
    enrollment_month = Column(Integer)
    cancellation_year = Column(Integer)
    cancellation_month = Column(Integer)


class FactFlightActivity(Base):
    __tablename__ = "fact_flight_activity"
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    loyalty_number = Column(Integer, ForeignKey("dim_customer.loyalty_number"))
    activity_year = Column(Integer)
    activity_month = Column(Integer)
    total_flights = Column(Integer)
    distance = Column(Float)
    points_accumulated = Column(Float)
    points_redeemed = Column(Float)
    date_key = Column(Date, ForeignKey("dim_calendar.date_key"))
    dollar_cost_points_redeemed = Column(Float)
    cost_per_point = Column(Float)
    avg_distance_per_flight = Column(Float)
    points_per_flight = Column(Float)
    is_redemption_month = Column(Integer)


class FactSatisfactionSurvey(Base):
    __tablename__ = "fact_satisfaction_survey"
    survey_id = Column(Integer, primary_key=True)
    gender = Column(String(10))
    age = Column(Integer)
    customer_type = Column(String(50))
    type_of_travel = Column(String(50))
    flight_class = Column(String(50))
    flight_distance = Column(Integer)
    departure_delay_min = Column(Integer)
    arrival_delay_min = Column(Integer)
    convenience_score = Column(Integer)
    online_booking_score = Column(Integer)
    check_in_score = Column(Integer)
    online_boarding_score = Column(Integer)
    gate_location_score = Column(Integer)
    on_board_service_score = Column(Integer)
    seat_comfort_score = Column(Integer)
    leg_room_score = Column(Integer)
    cleanliness_score = Column(Integer)
    food_drink_score = Column(Integer)
    in_flight_service_score = Column(Integer)
    wifi_score = Column(Integer)
    entertainment_score = Column(Integer)
    baggage_handling_score = Column(Integer)
    overall_satisfaction = Column(String(20))
    comment_text = Column(Text)