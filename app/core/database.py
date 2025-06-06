"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Generator

from .config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database Models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    location = Column(String(100))
    preferred_language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    disease_scans = relationship("DiseaseScan", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class DiseaseScan(Base):
    """Disease scan results model"""
    __tablename__ = "disease_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    predicted_disease = Column(String(100))
    confidence_score = Column(Float)
    treatment_recommendation = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="disease_scans")

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column(Text)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class WeatherData(Base):
    """Weather data cache model"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    description = Column(String(100))
    visibility = Column(Float)
    uv_index = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

class SoilData(Base):
    """Soil data model"""
    __tablename__ = "soil_data"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    ph_level = Column(Float)
    moisture_content = Column(Float)
    nitrogen_level = Column(Float)
    phosphorus_level = Column(Float)
    potassium_level = Column(Float)
    organic_matter = Column(Float)
    soil_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

# New Roadmap Features Models

class CropYieldPrediction(Base):
    """Crop yield prediction model"""
    __tablename__ = "crop_yield_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_type = Column(String(100), nullable=False)
    field_size_hectares = Column(Float, nullable=False)
    planting_date = Column(DateTime, nullable=False)
    expected_harvest_date = Column(DateTime)
    predicted_yield_kg = Column(Float)
    confidence_score = Column(Float)
    weather_factors = Column(JSON)  # Store weather impact factors
    soil_factors = Column(JSON)     # Store soil quality factors
    historical_data = Column(JSON)  # Store historical yield data
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class IoTSensorData(Base):
    """IoT sensor data model"""
    __tablename__ = "iot_sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sensor_id = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # temperature, humidity, soil_moisture, etc.
    location_name = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    battery_level = Column(Float)
    signal_strength = Column(Float)
    sensor_metadata = Column(JSON)  # Additional sensor-specific data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class MarketplaceListing(Base):
    """Marketplace listing model"""
    __tablename__ = "marketplace_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_type = Column(String(20), nullable=False)  # 'product', 'service', 'equipment'
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)
    price = Column(Float)
    currency = Column(String(10), default="USD")
    quantity_available = Column(Integer)
    unit = Column(String(20))  # kg, tons, pieces, etc.
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    images = Column(JSON)  # Array of image URLs
    contact_info = Column(JSON)  # Phone, email, etc.
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    seller = relationship("User")

class CommunityPost(Base):
    """Community forum post model"""
    __tablename__ = "community_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # 'question', 'tip', 'discussion', 'news'
    tags = Column(JSON)  # Array of tags
    images = Column(JSON)  # Array of image URLs
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    likes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_solved = Column(Boolean, default=False)  # For questions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User")
    replies = relationship("CommunityReply", back_populates="post")

class CommunityReply(Base):
    """Community forum reply model"""
    __tablename__ = "community_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(JSON)  # Array of image URLs
    likes_count = Column(Integer, default=0)
    is_solution = Column(Boolean, default=False)  # Mark as solution for questions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    post = relationship("CommunityPost", back_populates="replies")
    author = relationship("User")

class OfflineData(Base):
    """Offline data cache model"""
    __tablename__ = "offline_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_type = Column(String(50), nullable=False)  # 'weather', 'soil', 'disease_model', etc.
    data_key = Column(String(200), nullable=False)  # Unique identifier for the data
    data_content = Column(JSON, nullable=False)  # The actual cached data
    location_hash = Column(String(100))  # Hash of lat/lng for location-based data
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class PrecisionField(Base):
    """Precision agriculture field model"""
    __tablename__ = "precision_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    field_name = Column(String(200), nullable=False)
    field_boundaries = Column(JSON, nullable=False)  # GeoJSON polygon coordinates
    total_area_hectares = Column(Float, nullable=False)
    crop_type = Column(String(100))
    planting_date = Column(DateTime)
    expected_harvest_date = Column(DateTime)
    soil_zones = Column(JSON)  # Different soil management zones
    elevation_data = Column(JSON)  # Elevation map data
    drainage_patterns = Column(JSON)  # Water drainage analysis
    historical_yield_data = Column(JSON)  # Historical yield maps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    precision_applications = relationship("PrecisionApplication", back_populates="field")
    field_monitoring = relationship("FieldMonitoring", back_populates="field")

class PrecisionApplication(Base):
    """Variable rate application records"""
    __tablename__ = "precision_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("precision_fields.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application_type = Column(String(50), nullable=False)  # 'fertilizer', 'pesticide', 'seed', 'water'
    product_name = Column(String(200))
    application_rate_map = Column(JSON, nullable=False)  # Variable rate map
    total_quantity_applied = Column(Float)
    unit = Column(String(20))  # kg/ha, L/ha, etc.
    application_date = Column(DateTime, nullable=False)
    weather_conditions = Column(JSON)  # Weather during application
    equipment_used = Column(String(200))
    cost_per_unit = Column(Float)
    total_cost = Column(Float)
    effectiveness_score = Column(Float)  # Post-application assessment
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    field = relationship("PrecisionField", back_populates="precision_applications")
    user = relationship("User")

class FieldMonitoring(Base):
    """Field monitoring and sensor data"""
    __tablename__ = "field_monitoring"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("precision_fields.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    monitoring_type = Column(String(50), nullable=False)  # 'ndvi', 'soil_moisture', 'temperature', 'growth_stage'
    data_points = Column(JSON, nullable=False)  # Spatial data points with values
    measurement_date = Column(DateTime, nullable=False)
    data_source = Column(String(100))  # 'satellite', 'drone', 'ground_sensor', 'manual'
    resolution_meters = Column(Float)  # Spatial resolution
    analysis_results = Column(JSON)  # Processed analysis results
    anomalies_detected = Column(JSON)  # Areas requiring attention
    recommendations = Column(JSON)  # Automated recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    field = relationship("PrecisionField", back_populates="field_monitoring")
    user = relationship("User")

class ClimateRiskAssessment(Base):
    """Climate risk assessment model"""
    __tablename__ = "climate_risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    assessment_period_years = Column(Integer, default=10)
    crop_types = Column(JSON, nullable=False)  # List of crops to assess
    
    # Climate risk factors
    temperature_trends = Column(JSON)  # Historical and projected temperature data
    precipitation_trends = Column(JSON)  # Rainfall patterns and projections
    extreme_weather_frequency = Column(JSON)  # Drought, flood, storm frequency
    seasonal_shifts = Column(JSON)  # Changes in growing seasons
    
    # Risk scores (0-100)
    drought_risk_score = Column(Float)
    flood_risk_score = Column(Float)
    heat_stress_risk_score = Column(Float)
    frost_risk_score = Column(Float)
    pest_disease_risk_score = Column(Float)
    overall_risk_score = Column(Float)
    
    # Vulnerability assessment
    soil_vulnerability = Column(JSON)  # Soil degradation risks
    water_resource_vulnerability = Column(JSON)  # Water availability risks
    crop_vulnerability = Column(JSON)  # Crop-specific vulnerabilities
    
    assessment_date = Column(DateTime, nullable=False)
    next_assessment_due = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    adaptation_strategies = relationship("ClimateAdaptationStrategy", back_populates="risk_assessment")

class ClimateAdaptationStrategy(Base):
    """Climate adaptation strategies and plans"""
    __tablename__ = "climate_adaptation_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_assessment_id = Column(Integer, ForeignKey("climate_risk_assessments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_name = Column(String(200), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # 'crop_diversification', 'water_management', 'soil_conservation', etc.
    
    # Strategy details
    description = Column(Text, nullable=False)
    implementation_steps = Column(JSON, nullable=False)  # Step-by-step implementation
    timeline_months = Column(Integer)  # Implementation timeline
    estimated_cost = Column(Float)
    expected_benefits = Column(JSON)  # Expected outcomes and benefits
    
    # Risk mitigation
    risks_addressed = Column(JSON)  # Which climate risks this strategy addresses
    effectiveness_score = Column(Float)  # Predicted effectiveness (0-100)
    
    # Implementation tracking
    implementation_status = Column(String(20), default="planned")  # planned, in_progress, completed, paused
    progress_percentage = Column(Float, default=0.0)
    actual_cost = Column(Float)
    actual_benefits = Column(JSON)  # Measured outcomes
    lessons_learned = Column(Text)
    
    # Monitoring and evaluation
    monitoring_indicators = Column(JSON)  # KPIs to track
    evaluation_schedule = Column(JSON)  # When to evaluate progress
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    risk_assessment = relationship("ClimateRiskAssessment", back_populates="adaptation_strategies")
    user = relationship("User")

class ClimateMonitoring(Base):
    """Climate monitoring and early warning system"""
    __tablename__ = "climate_monitoring"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Monitoring data
    monitoring_date = Column(DateTime, nullable=False)
    temperature_data = Column(JSON)  # Current and recent temperature readings
    precipitation_data = Column(JSON)  # Rainfall measurements
    humidity_data = Column(JSON)  # Humidity levels
    wind_data = Column(JSON)  # Wind speed and direction
    soil_temperature = Column(Float)
    soil_moisture_levels = Column(JSON)  # Multiple depth measurements
    
    # Derived indicators
    growing_degree_days = Column(Float)
    evapotranspiration_rate = Column(Float)
    water_stress_index = Column(Float)
    heat_stress_index = Column(Float)
    
    # Alerts and warnings
    active_alerts = Column(JSON)  # Current weather/climate alerts
    risk_warnings = Column(JSON)  # Predicted risks in coming days
    recommended_actions = Column(JSON)  # Immediate actions to take
    
    # Data sources
    data_sources = Column(JSON)  # Weather stations, satellites, sensors used
    data_quality_score = Column(Float)  # Reliability of the data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

# Dependency to get database session
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)