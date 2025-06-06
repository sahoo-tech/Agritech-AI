#!/usr/bin/env python3
"""
AgriTech Assistant - Streamlit Frontend
A comprehensive agricultural assistance platform
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any
import base64
from io import BytesIO
from PIL import Image

# Configuration
BASE_API_URL = "http://localhost:8000/api"
WEATHER_API_URL = f"{BASE_API_URL}/weather"
AUTH_API_URL = f"{BASE_API_URL}/auth"
DISEASE_API_URL = f"{BASE_API_URL}/disease"
CHAT_API_URL = f"{BASE_API_URL}/chat"

def check_api_connection() -> bool:
    """Check if API server is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def show_api_status():
    """Show API connection status in sidebar"""
    with st.sidebar:
        if check_api_connection():
            st.success("🟢 API Server: Connected")
            st.caption("Real-time data available")
        else:
            st.error("🔴 API Server: Disconnected")
            st.caption("Using simulated data")
            with st.expander("🔧 How to start API server"):
                st.code("python run.py", language="bash")
                st.caption("Then refresh this page")

# Page configuration
st.set_page_config(
    page_title="🌱 AgriTech Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def get_auth_headers():
    """Get authentication headers for API requests"""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

def login_user(username: str, password: str) -> bool:
    """Login user and store authentication token"""
    try:
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(
            f"{AUTH_API_URL}/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            st.session_state.authenticated = True
            
            # Get user info
            user_response = requests.get(
                f"{AUTH_API_URL}/me",
                headers=get_auth_headers(),
                timeout=5
            )
            if user_response.status_code == 200:
                st.session_state.user_info = user_response.json()
            
            st.success("✅ Login successful!")
            return True
        else:
            st.error(f"❌ Login failed: Invalid credentials")
            return False
    except requests.exceptions.ConnectionError:
        st.error("🔌 **API Server Not Running**")
        st.info("💡 **Solution:** Start the API server first with `python run.py`, then refresh this page")
        st.info("🔄 **Alternative:** Use demo mode with `streamlit run demo_frontend.py`")
        return False
    except requests.exceptions.Timeout:
        st.error("⏱️ **Connection Timeout**")
        st.info("💡 Please check if the API server is running and try again")
        return False
    except Exception as e:
        st.error(f"❌ **Connection Error:** {str(e)}")
        st.info("💡 **Solution:** Make sure the API server is running with `python run.py`")
        return False

def register_user(username: str, email: str, password: str, full_name: str, location: str) -> bool:
    """Register new user"""
    try:
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "location": location
        }
        response = requests.post(
            f"{AUTH_API_URL}/register",
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            st.success("✅ Registration successful! Please login.")
            return True
        elif response.status_code == 400:
            st.error("❌ Registration failed: Username or email already exists")
            return False
        else:
            st.error(f"❌ Registration failed: Server error")
            return False
    except requests.exceptions.ConnectionError:
        st.error("🔌 **API Server Not Running**")
        st.info("💡 **Solution:** Start the API server first with `python run.py`, then refresh this page")
        st.info("🔄 **Alternative:** Use demo mode with `streamlit run demo_frontend.py`")
        return False
    except requests.exceptions.Timeout:
        st.error("⏱️ **Connection Timeout**")
        st.info("💡 Please check if the API server is running and try again")
        return False
    except Exception as e:
        st.error(f"❌ **Connection Error:** {str(e)}")
        st.info("💡 **Solution:** Make sure the API server is running with `python run.py`")
        return False

def logout_user():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.chat_history = []
    st.rerun()

def get_weather_data(latitude: float, longitude: float) -> Optional[Dict]:
    """Get weather data from API"""
    try:
        data = {"latitude": latitude, "longitude": longitude}
        
        # Try authenticated endpoint first, then public endpoint
        headers = get_auth_headers()
        endpoint = f"{WEATHER_API_URL}/current" if headers else f"{WEATHER_API_URL}/public/current"
        
        response = requests.post(endpoint, json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401 and headers:
            # Try public endpoint if authentication fails
            response = requests.post(f"{WEATHER_API_URL}/public/current", json=data, timeout=5)
            if response.status_code == 200:
                return response.json()
        
        st.error(f"Weather API error: {response.status_code}")
        return None
    except requests.exceptions.ConnectionError:
        # Backend server is not running - provide fallback data
        return get_fallback_weather_data(latitude, longitude)
    except requests.exceptions.Timeout:
        st.warning("Weather service is slow to respond. Using cached data.")
        return get_fallback_weather_data(latitude, longitude)
    except Exception as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return get_fallback_weather_data(latitude, longitude)

def get_fallback_weather_data(latitude: float, longitude: float) -> Dict:
    """Provide fallback weather data when API is unavailable"""
    import random
    import math
    from datetime import datetime
    
    # Generate realistic mock data based on location
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    hour = now.hour
    
    # Seasonal variation
    seasonal_factor = math.sin((day_of_year - 80) * 2 * math.pi / 365)
    
    # Base temperature varies by latitude
    if abs(latitude) < 23.5:  # Tropical
        base_temp = 28 + seasonal_factor * 4
    elif abs(latitude) < 40:  # Subtropical  
        base_temp = 22 + seasonal_factor * 10
    elif abs(latitude) < 60:  # Temperate
        base_temp = 15 + seasonal_factor * 15
    else:  # Polar
        base_temp = 5 + seasonal_factor * 20
    
    # Daily temperature variation
    daily_variation = 4 * math.sin((hour - 6) * math.pi / 12)
    temperature = base_temp + daily_variation + random.uniform(-3, 3)
    
    # Generate realistic humidity and wind speed
    humidity = random.randint(40, 80)
    wind_speed = round(random.uniform(3, 18), 1)
    
    return {
        "current": {
            "temperature": round(temperature, 1),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "condition": "Demo Data",
            "description": "Offline mode - Start backend server for real data"
        },
        "data_source": "🔄 Offline Demo Data",
        "note": "Start the backend server (python main.py) for real weather data",
        "last_updated": now.isoformat()
    }

def get_soil_data(latitude: float, longitude: float) -> Optional[Dict]:
    """Get soil data from API with fallback to local generation"""
    try:
        data = {"latitude": latitude, "longitude": longitude}
        
        # Try authenticated endpoint first, then public endpoint
        headers = get_auth_headers()
        endpoint = f"{WEATHER_API_URL}/soil" if headers else f"{WEATHER_API_URL}/public/soil"
        
        response = requests.post(endpoint, json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401 and headers:
            # Try public endpoint if authentication fails
            response = requests.post(f"{WEATHER_API_URL}/public/soil", json=data, timeout=5)
            if response.status_code == 200:
                return response.json()
        
        # If API fails, generate fallback data
        st.warning("🔄 API unavailable, using simulated soil data")
        return generate_fallback_soil_data(latitude, longitude)
        
    except requests.exceptions.ConnectionError:
        st.warning("🔄 API server not running, using simulated soil data")
        return generate_fallback_soil_data(latitude, longitude)
    except requests.exceptions.Timeout:
        st.warning("🔄 API timeout, using simulated soil data")
        return generate_fallback_soil_data(latitude, longitude)
    except Exception as e:
        st.warning(f"🔄 Error connecting to API: {str(e)}, using simulated soil data")
        return generate_fallback_soil_data(latitude, longitude)


def generate_fallback_soil_data(latitude: float, longitude: float) -> Dict:
    """Generate realistic soil data based on location"""
    import random
    from datetime import datetime
    
    # Determine soil type based on latitude (climate zones)
    if abs(latitude) < 23.5:  # Tropical
        soil_types = ["clay", "sandy", "loam"]
        weights = [0.4, 0.4, 0.2]
    elif abs(latitude) < 40:  # Temperate
        soil_types = ["loam", "clay", "silt"]
        weights = [0.5, 0.3, 0.2]
    else:  # Cold regions
        soil_types = ["peat", "silt", "clay"]
        weights = [0.4, 0.3, 0.3]
    
    soil_type = random.choices(soil_types, weights=weights)[0]
    
    # pH varies by soil type and climate
    ph_ranges = {
        "clay": (6.0, 7.5),
        "sandy": (5.5, 6.5), 
        "loam": (6.0, 7.0),
        "silt": (6.5, 7.5),
        "peat": (4.5, 6.0)
    }
    
    ph_level = round(random.uniform(*ph_ranges[soil_type]), 1)
    
    # Moisture content varies by soil type and season
    moisture_ranges = {
        "clay": (40, 70),
        "sandy": (15, 35),
        "loam": (30, 50), 
        "silt": (35, 60),
        "peat": (60, 85)
    }
    
    moisture_content = round(random.uniform(*moisture_ranges[soil_type]), 1)
    
    # Temperature based on latitude (simplified)
    base_temp = 25 - abs(latitude) * 0.6
    soil_temp = round(base_temp + random.uniform(-3, 3), 1)
    
    # Nutrients based on soil type
    nutrient_levels = {
        "clay": {"nitrogen": "high", "phosphorus": "medium", "potassium": "high"},
        "sandy": {"nitrogen": "low", "phosphorus": "low", "potassium": "medium"},
        "loam": {"nitrogen": "high", "phosphorus": "high", "potassium": "high"},
        "silt": {"nitrogen": "medium", "phosphorus": "high", "potassium": "medium"},
        "peat": {"nitrogen": "very_high", "phosphorus": "low", "potassium": "low"}
    }
    
    characteristics = {
        "clay": {
            "drainage": "poor",
            "water_retention": "excellent", 
            "workability": "difficult",
            "fertility": "high"
        },
        "sandy": {
            "drainage": "excellent",
            "water_retention": "poor",
            "workability": "easy", 
            "fertility": "low"
        },
        "loam": {
            "drainage": "good",
            "water_retention": "good",
            "workability": "easy",
            "fertility": "excellent"
        },
        "silt": {
            "drainage": "moderate",
            "water_retention": "good", 
            "workability": "moderate",
            "fertility": "good"
        },
        "peat": {
            "drainage": "poor",
            "water_retention": "excellent",
            "workability": "difficult",
            "fertility": "very_high"
        }
    }
    
    recommendations = {
        "clay": [
            "Add organic matter to improve drainage",
            "Avoid working when wet to prevent compaction",
            "Consider raised beds for better drainage",
            "Plant cover crops to improve structure"
        ],
        "sandy": [
            "Add compost to improve water retention",
            "Use mulch to reduce water evaporation", 
            "Apply fertilizer more frequently",
            "Plant drought-tolerant crops"
        ],
        "loam": [
            "Maintain organic matter with compost",
            "Practice crop rotation",
            "Minimal tillage to preserve structure",
            "Ideal for most crops"
        ],
        "silt": [
            "Improve drainage with organic matter",
            "Avoid compaction when wet",
            "Add coarse organic matter",
            "Good for vegetables and grains"
        ],
        "peat": [
            "Monitor pH levels regularly",
            "Add lime if too acidic",
            "Excellent for acid-loving plants",
            "Ensure adequate drainage"
        ]
    }
    
    return {
        "soil_type": soil_type,
        "ph_level": ph_level,
        "moisture_content": moisture_content,
        "temperature": soil_temp,
        "nutrients": nutrient_levels[soil_type],
        "characteristics": characteristics[soil_type],
        "recommendations": recommendations[soil_type],
        "data_source": "🔄 Simulated Data (Start API server for real-time data)",
        "fallback_data": True,
        "last_updated": datetime.now().isoformat(),
        "location": {
            "latitude": latitude,
            "longitude": longitude
        }
    }

def get_comprehensive_data(latitude: float, longitude: float) -> Optional[Dict]:
    """Get comprehensive agricultural data"""
    try:
        data = {"latitude": latitude, "longitude": longitude}
        
        # Try authenticated endpoint first, then public endpoint
        headers = get_auth_headers()
        endpoint = f"{WEATHER_API_URL}/comprehensive" if headers else f"{WEATHER_API_URL}/public/comprehensive"
        
        response = requests.post(endpoint, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401 and headers:
            # Try public endpoint if authentication fails
            response = requests.post(f"{WEATHER_API_URL}/public/comprehensive", json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
        elif response.status_code == 403:
            # Handle forbidden error - try public endpoint
            st.warning("Authentication required for full features. Using public data.")
            response = requests.post(f"{WEATHER_API_URL}/public/comprehensive", json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
        
        st.error(f"Comprehensive data API error: {response.status_code}")
        return None
    except requests.exceptions.ConnectionError:
        st.warning("Backend server not available. Please start the backend server.")
        return None
    except requests.exceptions.Timeout:
        st.warning("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Error fetching comprehensive data: {str(e)}")
        return None

def analyze_plant_disease(image_file, latitude: float, longitude: float) -> Optional[Dict]:
    """Analyze plant disease from uploaded image"""
    try:
        files = {"image": image_file}
        data = {"latitude": latitude, "longitude": longitude}
        
        # Try authenticated endpoint first, then public endpoint
        headers = get_auth_headers()
        endpoint = f"{DISEASE_API_URL}/analyze" if headers else f"{DISEASE_API_URL}/public/analyze"
        
        response = requests.post(endpoint, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401 and headers:
            # Try public endpoint if authentication fails
            response = requests.post(f"{DISEASE_API_URL}/public/analyze", files=files, data=data)
            if response.status_code == 200:
                return response.json()
        
        st.error(f"Disease analysis error: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error analyzing plant disease: {str(e)}")
        return None

def send_chat_message(message: str, language: str = "en") -> Optional[Dict]:
    """Send message to AI chatbot"""
    try:
        data = {
            "message": message,
            "language": language,
            "context": {}
        }
        
        response = requests.post(
            f"{CHAT_API_URL}/message",
            json=data,
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Chat API error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error sending chat message: {str(e)}")
        return None

def show_login_page():
    """Display login/registration page"""
    st.title("🌱 Welcome to AgriTech Assistant")
    st.markdown("### Your AI-powered agricultural companion")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if username and password:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        st.subheader("Create new account")
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_full_name = st.text_input("Full Name", key="reg_full_name")
            reg_location = st.text_input("Location (City, Country)", key="reg_location")
            submit_register = st.form_submit_button("Register")
            
            if submit_register:
                if all([reg_username, reg_email, reg_password, reg_full_name, reg_location]):
                    register_user(reg_username, reg_email, reg_password, reg_full_name, reg_location)
                else:
                    st.error("Please fill in all fields")

def show_dashboard():
    """Display main dashboard"""
    # Enhanced CSS for better presentation
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57, #32CD32);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #2E8B57;
        margin-bottom: 1rem;
    }
    .weather-card {
        background: linear-gradient(135deg, #87CEEB, #4682B4);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .soil-card {
        background: linear-gradient(135deg, #DEB887, #8B4513);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .alert-card {
        background: linear-gradient(135deg, #FFB6C1, #DC143C);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .success-card {
        background: linear-gradient(135deg, #98FB98, #228B22);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌾 AgriTech Assistant Dashboard</h1>
        <p>Your AI-Powered Agricultural Companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🌱 Navigation")
        
        # User info
        if st.session_state.user_info:
            st.success(f"👤 Welcome, {st.session_state.user_info.get('full_name', 'User')}!")
        else:
            st.info("👤 Using Guest Mode")
        
        if st.session_state.authenticated and st.button("🚪 Logout"):
            logout_user()
        
        st.markdown("---")
        
        # Location input with better styling
        st.subheader("📍 Farm Location")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=20.5937, format="%.4f", help="Enter your farm's latitude")
        with col2:
            longitude = st.number_input("Longitude", value=78.9629, format="%.4f", help="Enter your farm's longitude")
        
        if st.button("📍 Use Current Location", help="Get your current GPS coordinates"):
            st.info("🔄 Geolocation feature would be implemented here")
        
        # Quick stats
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        
        # Get weather data for quick stats
        weather_data = get_weather_data(latitude, longitude)
        if weather_data and weather_data.get('current'):
            current = weather_data['current']
            st.metric("🌡️ Temperature", f"{current.get('temperature', 'N/A')}°C")
            st.metric("💧 Humidity", f"{current.get('humidity', 'N/A')}%")
            st.metric("💨 Wind Speed", f"{current.get('wind_speed', 'N/A')} km/h")
            
            # Show data source info
            if weather_data.get('data_source'):
                st.caption(weather_data['data_source'])
            if weather_data.get('note'):
                st.info(weather_data['note'])
        else:
            st.warning("Unable to load weather data. Please check your connection.")
    
    # Main content with improved layout
    # Create tabs for different features
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🌤️ Weather & Soil", 
        "🔍 Disease Detection", 
        "💬 AI Assistant", 
        "📊 Analytics & Reports",
        "🌾 Crop Yield Prediction",
        "📡 IoT Sensors",
        "🛒 Marketplace",
        "👥 Community"
    ])
    
    with tab1:
        show_weather_soil_tab(latitude, longitude)
    
    with tab2:
        show_disease_detection_tab(latitude, longitude)
    
    with tab3:
        show_ai_assistant_tab()
    
    with tab4:
        show_analytics_tab(latitude, longitude)
    
    with tab5:
        show_crop_yield_tab(latitude, longitude)
    
    with tab6:
        show_iot_sensors_tab()
    
    with tab7:
        show_marketplace_tab()
    
    with tab8:
        show_community_tab()

def show_weather_soil_tab(latitude: float, longitude: float):
    """Display weather and soil information with enhanced UI"""
    
    # Show demo data notice
    st.info("""
    📢 **Demo Mode Active**: You're currently viewing simulated agricultural data. 
    
    **To get real data:**
    1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
    2. Add it to your `.env` file: `WEATHER_API_KEY=your_key_here`
    3. Restart the application
    
    The demo data is realistic and updates dynamically based on your location and time.
    """)
    
    # Auto-fetch data on load
    if 'weather_data' not in st.session_state:
        with st.spinner("🌤️ Loading weather data..."):
            weather_data = get_weather_data(latitude, longitude)
            if weather_data:
                st.session_state.weather_data = weather_data
    
    if 'soil_data' not in st.session_state:
        with st.spinner("🌱 Loading soil data..."):
            soil_data = get_soil_data(latitude, longitude)
            if soil_data:
                st.session_state.soil_data = soil_data
    
    # Refresh buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Weather", use_container_width=True):
            with st.spinner("Fetching weather data..."):
                weather_data = get_weather_data(latitude, longitude)
                if weather_data:
                    st.session_state.weather_data = weather_data
                    st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Soil", use_container_width=True):
            with st.spinner("Fetching soil data..."):
                soil_data = get_soil_data(latitude, longitude)
                if soil_data:
                    st.session_state.soil_data = soil_data
                    st.rerun()
    
    # Weather Section
    if hasattr(st.session_state, 'weather_data') and st.session_state.weather_data:
        weather = st.session_state.weather_data
        current = weather.get('current', {})
        
        st.markdown("""
        <div class="weather-card">
            <h3>🌤️ Current Weather Conditions</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Weather metrics in a nice grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = current.get('temperature', 'N/A')
            st.metric(
                label="🌡️ Temperature", 
                value=f"{temp}°C" if temp != 'N/A' else 'N/A',
                help="Current air temperature"
            )
        
        with col2:
            humidity = current.get('humidity', 'N/A')
            st.metric(
                label="💧 Humidity", 
                value=f"{humidity}%" if humidity != 'N/A' else 'N/A',
                help="Relative humidity percentage"
            )
        
        with col3:
            wind_speed = current.get('wind_speed', 'N/A')
            st.metric(
                label="💨 Wind Speed", 
                value=f"{wind_speed} km/h" if wind_speed != 'N/A' else 'N/A',
                help="Current wind speed"
            )
        
        with col4:
            pressure = current.get('pressure', 'N/A')
            st.metric(
                label="📊 Pressure", 
                value=f"{pressure} hPa" if pressure != 'N/A' else 'N/A',
                help="Atmospheric pressure"
            )
        
        # Additional weather info
        col1, col2, col3 = st.columns(3)
        with col1:
            condition = current.get('condition', 'N/A')
            st.info(f"☁️ **Weather Condition:** {condition}")
        
        with col2:
            feels_like = current.get('feels_like', 'N/A')
            st.info(f"🌡️ **Feels Like:** {feels_like}°C" if feels_like != 'N/A' else "🌡️ **Feels Like:** N/A")
        
        with col3:
            data_source = weather.get('data_source', 'Unknown')
            if 'Demo Data' in data_source:
                st.warning(f"📊 {data_source}")
            else:
                st.success(f"📊 **Data Source:** Live API")
        
        # Weather alerts
        alerts = weather.get('alerts', [])
        if alerts:
            st.markdown("""
            <div class="alert-card">
                <h4>⚠️ Weather Alerts</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for alert in alerts:
                severity = alert.get('severity', 'medium')
                alert_type = alert.get('type', 'Alert')
                message = alert.get('message', 'No details available')
                
                if severity == 'high':
                    st.error(f"🚨 **{alert_type}**: {message}")
                elif severity == 'medium':
                    st.warning(f"⚠️ **{alert_type}**: {message}")
                else:
                    st.info(f"ℹ️ **{alert_type}**: {message}")
    
    else:
        st.warning("🌤️ Weather data not available. Please check your connection and try refreshing.")
    
    st.markdown("---")
    
    # Soil Section
    if hasattr(st.session_state, 'soil_data') and st.session_state.soil_data:
        soil = st.session_state.soil_data
        
        st.markdown("""
        <div class="soil-card">
            <h3>🌱 Soil Analysis Report</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Soil metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            moisture = soil.get('moisture_content', 'N/A')
            st.metric(
                label="💧 Soil Moisture", 
                value=f"{moisture}%" if moisture != 'N/A' else 'N/A',
                help="Current soil moisture content"
            )
        
        with col2:
            ph = soil.get('ph_level', 'N/A')
            st.metric(
                label="⚗️ pH Level", 
                value=f"{ph}" if ph != 'N/A' else 'N/A',
                help="Soil acidity/alkalinity level"
            )
        
        with col3:
            soil_temp = soil.get('temperature', 'N/A')
            st.metric(
                label="🌡️ Soil Temperature", 
                value=f"{soil_temp}°C" if soil_temp != 'N/A' else 'N/A',
                help="Current soil temperature"
            )
        
        with col4:
            soil_type = soil.get('soil_type', 'N/A')
            st.metric(
                label="🏔️ Soil Type", 
                value=soil_type,
                help="Identified soil type"
            )
        
        # Soil recommendations
        recommendations = soil.get('recommendations', [])
        if recommendations:
            st.markdown("""
            <div class="success-card">
                <h4>💡 Soil Recommendations</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for i, rec in enumerate(recommendations, 1):
                st.success(f"**{i}.** {rec}")
        
        # Nutrient information
        nutrients = soil.get('nutrients', {})
        if nutrients:
            st.subheader("🧪 Nutrient Analysis")
            
            nutrient_cols = st.columns(len(nutrients))
            for i, (nutrient, data) in enumerate(nutrients.items()):
                with nutrient_cols[i]:
                    level = data.get('level', 'N/A') if isinstance(data, dict) else data
                    status = data.get('status', 'Unknown') if isinstance(data, dict) else 'Unknown'
                    
                    # Color code based on status
                    if status.lower() == 'optimal':
                        st.success(f"**{nutrient.title()}**\n{level}")
                    elif status.lower() == 'low':
                        st.warning(f"**{nutrient.title()}**\n{level}")
                    elif status.lower() == 'high':
                        st.error(f"**{nutrient.title()}**\n{level}")
                    else:
                        st.info(f"**{nutrient.title()}**\n{level}")
    
    else:
        st.warning("🌱 Soil data not available. Please check your connection and try refreshing.")

def show_disease_detection_tab(latitude: float, longitude: float):
    """Display disease detection interface"""
    st.header("🔍 Plant Disease Detection")
    
    # Add demo notice
    st.info("""
    📢 **Demo Mode**: Disease detection is currently using mock analysis results.
    
    **To enable real AI detection:**
    1. Add trained model files to the `models/` directory
    2. Configure `DISEASE_MODEL_PATH` in `.env`
    3. Optionally add `OPENAI_API_KEY` for enhanced analysis
    """)
    
    # Image input options
    st.subheader("📸 Choose Image Source")
    
    input_method = st.radio(
        "Select how you want to provide the plant image:",
        ["📁 Upload from Device", "📷 Take Photo with Camera"],
        horizontal=True
    )
    
    uploaded_file = None
    camera_image = None
    
    if input_method == "📁 Upload from Device":
        uploaded_file = st.file_uploader(
            "Upload a plant image for disease analysis",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of the plant leaf or affected area"
        )
    
    elif input_method == "📷 Take Photo with Camera":
        st.write("📷 **Camera Capture**")
        camera_image = st.camera_input(
            "Take a photo of the plant",
            help="Position the plant leaf or affected area clearly in the camera view"
        )
    
    # Process the image (either uploaded or from camera)
    image_to_analyze = uploaded_file or camera_image
    
    if image_to_analyze is not None:
        # Display the image
        image = Image.open(image_to_analyze)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(image, caption="Image for Analysis", use_column_width=True)
        
        with col2:
            st.write("**Image Details:**")
            st.write(f"📏 Size: {image.size[0]} x {image.size[1]} pixels")
            st.write(f"📊 Format: {image.format}")
            st.write(f"🎨 Mode: {image.mode}")
            
            # Image quality tips
            st.write("**💡 Tips for better analysis:**")
            st.write("• Ensure good lighting")
            st.write("• Focus on affected areas")
            st.write("• Avoid blurry images")
            st.write("• Include leaf details")
        
        st.markdown("---")
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Analyze for Plant Diseases", use_container_width=True, type="primary"):
                with st.spinner("🤖 AI is analyzing the plant image..."):
                    # Reset file pointer if it's an uploaded file
                    if hasattr(image_to_analyze, 'seek'):
                        image_to_analyze.seek(0)
                    result = analyze_plant_disease(image_to_analyze, latitude, longitude)
                
                if result:
                    st.success("✅ Analysis completed successfully!")
                    
                    # Show data source
                    if result.get('demo_mode'):
                        st.info(f"📊 {result.get('data_source', 'Demo Analysis')}")
                    
                    # Main results
                    st.markdown("---")
                    
                    # Detection Results
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("🎯 Disease Detection Results")
                        
                        disease_name = result.get('predicted_disease', 'Unknown')
                        confidence = result.get('confidence', 0)
                        severity = result.get('severity', 'unknown')
                        
                        # Color code based on disease type and severity
                        if disease_name.lower() == 'healthy plant':
                            st.success(f"🌿 **{disease_name}**")
                            st.success(f"✅ Confidence: {confidence:.1%}")
                        else:
                            if severity == 'severe':
                                st.error(f"🚨 **Disease Detected: {disease_name}**")
                                st.error(f"⚠️ Severity: {severity.title()}")
                            elif severity == 'moderate':
                                st.warning(f"⚠️ **Disease Detected: {disease_name}**")
                                st.warning(f"📊 Severity: {severity.title()}")
                            else:
                                st.info(f"ℹ️ **Disease Detected: {disease_name}**")
                                st.info(f"📊 Severity: {severity.title()}")
                            
                            st.write(f"🎯 **Confidence**: {confidence:.1%}")
                        
                        # Description
                        if result.get('description'):
                            st.write(f"📝 **Description**: {result['description']}")
                    
                    with col2:
                        # Image Quality Assessment
                        st.subheader("📸 Image Quality")
                        
                        quality = result.get('image_quality', {})
                        quality_score = quality.get('quality_score', 0)
                        
                        if quality_score >= 85:
                            st.success(f"📊 Quality Score: {quality_score}/100")
                        elif quality_score >= 70:
                            st.warning(f"📊 Quality Score: {quality_score}/100")
                        else:
                            st.error(f"📊 Quality Score: {quality_score}/100")
                        
                        # Quality issues and recommendations
                        issues = quality.get('issues', [])
                        recommendations = quality.get('recommendations', [])
                        
                        if issues:
                            st.write("**Issues:**")
                            for issue in issues:
                                st.write(f"• {issue}")
                        
                        if recommendations:
                            st.write("**Tips:**")
                            for rec in recommendations:
                                st.write(f"• {rec}")
                    
                    # Treatment and Prevention
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("💊 Treatment Plan")
                        
                        treatment_plan = result.get('treatment_plan', {})
                        
                        if treatment_plan.get('immediate_actions'):
                            st.write("**🚨 Immediate Actions:**")
                            for action in treatment_plan['immediate_actions']:
                                st.write(f"• {action}")
                        
                        if treatment_plan.get('weekly_care'):
                            st.write("**📅 Weekly Care:**")
                            for care in treatment_plan['weekly_care']:
                                st.write(f"• {care}")
                        
                        # Direct treatment
                        if result.get('treatment'):
                            st.write("**🔧 Primary Treatment:**")
                            st.write(f"• {result['treatment']}")
                    
                    with col2:
                        st.subheader("🛡️ Prevention Measures")
                        
                        prevention = result.get('prevention', [])
                        if prevention:
                            for measure in prevention:
                                st.write(f"• {measure}")
                        
                        if treatment_plan.get('preventive_measures'):
                            st.write("**🔄 Ongoing Prevention:**")
                            for measure in treatment_plan['preventive_measures']:
                                st.write(f"• {measure}")
                    
                    # Additional Info
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if result.get('scan_id'):
                            st.info(f"🆔 **Scan ID**: {result['scan_id']}")
                    
                    with col2:
                        if result.get('location'):
                            st.info(f"📍 **Location**: {result['location']}")
                    
                    with col3:
                        if result.get('created_at'):
                            from datetime import datetime
                            try:
                                dt = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
                                st.info(f"🕒 **Analyzed**: {dt.strftime('%H:%M:%S')}")
                            except:
                                st.info(f"🕒 **Analyzed**: Just now")
                
                else:
                    st.error("❌ Analysis failed. Please try again with a different image.")

def show_ai_assistant_tab():
    """Display AI assistant chat interface"""
    st.header("💬 AI Agricultural Assistant")
    
    # Language selection
    language = st.selectbox(
        "Select Language",
        ["en", "es", "fr", "de", "hi", "zh"],
        format_func=lambda x: {
            "en": "English", "es": "Spanish", "fr": "French", 
            "de": "German", "hi": "Hindi", "zh": "Chinese"
        }.get(x, x)
    )
    
    # Chat interface
    st.subheader("Chat with AI Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about agriculture..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Get AI response
        with st.spinner("AI is thinking..."):
            response = send_chat_message(prompt, language)
            
            if response and response.get('response'):
                ai_message = response['response']
                st.session_state.chat_history.append({"role": "assistant", "content": ai_message})
                st.chat_message("assistant").write(ai_message)
            else:
                error_msg = "Sorry, I couldn't process your request. Please try again."
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                st.chat_message("assistant").write(error_msg)

def show_analytics_tab(latitude: float, longitude: float):
    """Display analytics and insights"""
    st.header("📊 Agricultural Analytics")
    
    # Show authentication status
    if not st.session_state.authenticated:
        st.info("🔐 **Login for Enhanced Analytics**: Get personalized insights and historical data by logging in.")
    
    if st.button("📈 Get Comprehensive Analysis"):
        with st.spinner("Generating comprehensive analysis..."):
            data = get_comprehensive_data(latitude, longitude)
            
            if data:
                # Show data source info
                if data.get('data_source'):
                    st.caption(data['data_source'])
                
                # Location info
                if data.get('location'):
                    st.subheader("📍 Location Information")
                    location_info = data['location']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Latitude", f"{location_info['coordinates']['latitude']:.4f}")
                    with col2:
                        st.metric("Longitude", f"{location_info['coordinates']['longitude']:.4f}")
                    
                    if location_info.get('info') and not location_info['info'].get('error'):
                        info = location_info['info']
                        if info.get('formatted_address'):
                            st.write(f"**Address**: {info['formatted_address']}")
                
                # Weather trends
                if data.get('weather'):
                    st.subheader("🌤️ Weather Analysis")
                    weather = data['weather']
                    current = weather.get('current', {})
                    
                    # Current conditions
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🌡️ Temperature", f"{current.get('temperature', 'N/A')}°C")
                    with col2:
                        st.metric("💧 Humidity", f"{current.get('humidity', 'N/A')}%")
                    with col3:
                        st.metric("💨 Wind Speed", f"{current.get('wind_speed', 'N/A')} km/h")
                    with col4:
                        st.metric("🌤️ Condition", current.get('condition', 'N/A'))
                    
                    # Weather trends table
                    if weather.get('forecast_24h'):
                        forecast = weather['forecast_24h']
                        weather_df = pd.DataFrame([{
                            'Metric': 'Temperature',
                            'Current': current.get('temperature', 0),
                            'Trend': forecast.get('temperature_trend', 'stable'),
                            'Max (24h)': forecast.get('max_temp', 'N/A'),
                            'Min (24h)': forecast.get('min_temp', 'N/A')
                        }, {
                            'Metric': 'Humidity',
                            'Current': current.get('humidity', 0),
                            'Trend': forecast.get('humidity_trend', 'stable'),
                            'Max (24h)': 'N/A',
                            'Min (24h)': 'N/A'
                        }])
                        
                        st.dataframe(weather_df, use_container_width=True)
                
                # Soil analysis
                if data.get('soil'):
                    st.subheader("🌱 Soil Analysis")
                    soil = data['soil']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Soil Type", soil.get('soil_type', 'Unknown'))
                    with col2:
                        st.metric("pH Level", f"{soil.get('ph_level', 'N/A')}")
                    with col3:
                        st.metric("Moisture", f"{soil.get('moisture_content', 'N/A')}%")
                    
                    # Soil nutrients
                    if soil.get('nutrients'):
                        st.write("**Nutrient Levels:**")
                        nutrients = soil['nutrients']
                        nutrient_df = pd.DataFrame([
                            {'Nutrient': k.title(), 'Level': v.get('level', 'Unknown'), 'Status': v.get('status', 'Unknown')}
                            for k, v in nutrients.items()
                        ])
                        st.dataframe(nutrient_df, use_container_width=True)
                
                # Agricultural conditions
                if data.get('weather', {}).get('agricultural_conditions'):
                    st.subheader("🚜 Agricultural Conditions")
                    conditions = data['weather']['agricultural_conditions']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Planting Suitability", conditions.get('planting_suitability', 'Unknown'))
                    with col2:
                        st.metric("Irrigation Need", conditions.get('irrigation_need', 'Unknown'))
                    with col3:
                        st.metric("Pest Risk", conditions.get('pest_risk', 'Unknown'))
                    with col4:
                        st.metric("Disease Risk", conditions.get('disease_risk', 'Unknown'))
                
                # Farming recommendations
                if data.get('farming_recommendations'):
                    st.subheader("💡 Farming Recommendations")
                    recommendations = data['farming_recommendations']
                    
                    if recommendations.get('immediate_actions'):
                        st.write("**🚨 Immediate Actions:**")
                        for action in recommendations['immediate_actions']:
                            st.warning(f"• {action}")
                    
                    if recommendations.get('this_week'):
                        st.write("**📅 This Week:**")
                        for action in recommendations['this_week']:
                            st.info(f"• {action}")
                    
                    if recommendations.get('general_advice'):
                        st.write("**📋 General Advice:**")
                        for advice in recommendations['general_advice']:
                            st.success(f"• {advice}")
                
                # Alerts
                if data.get('weather', {}).get('alerts'):
                    st.subheader("⚠️ Weather Alerts")
                    alerts = data['weather']['alerts']
                    for alert in alerts:
                        if alert.get('severity') == 'high':
                            st.error(f"🚨 {alert.get('message', 'High priority alert')}")
                        elif alert.get('severity') == 'medium':
                            st.warning(f"⚠️ {alert.get('message', 'Medium priority alert')}")
                        else:
                            st.info(f"ℹ️ {alert.get('message', 'General alert')}")
                
                # Timestamp
                if data.get('timestamp'):
                    st.caption(f"Last updated: {data['timestamp']}")
            
            else:
                st.error("❌ Unable to fetch comprehensive data. Please check your connection and try again.")
                st.info("💡 **Troubleshooting Tips:**")
                st.write("• Make sure the backend server is running (`python main.py`)")
                st.write("• Check your internet connection")
                st.write("• Try refreshing the page")

def show_crop_yield_tab(latitude: float, longitude: float):
    """Display crop yield prediction interface"""
    st.header("🌾 Crop Yield Prediction")
    
    st.info("""
    📢 **Advanced Analytics Feature**: Predict crop yields based on environmental factors, soil conditions, and historical data.
    
    **Features:**
    - AI-powered yield forecasting
    - Weather impact analysis
    - Soil factor consideration
    - Personalized recommendations
    """)
    
    # Crop yield prediction form
    with st.form("crop_yield_form"):
        st.subheader("📝 Yield Prediction Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            crop_type = st.selectbox(
                "🌱 Crop Type",
                ["wheat", "rice", "corn", "soybeans", "tomatoes"],
                help="Select the crop you want to predict yield for"
            )
            
            field_size = st.number_input(
                "📏 Field Size (hectares)",
                min_value=0.1,
                max_value=1000.0,
                value=1.0,
                step=0.1,
                help="Enter the size of your field in hectares"
            )
        
        with col2:
            planting_date = st.date_input(
                "📅 Planting Date",
                help="Select the planned or actual planting date"
            )
            
            st.write("📍 **Location**")
            st.write(f"Latitude: {latitude:.4f}")
            st.write(f"Longitude: {longitude:.4f}")
        
        submitted = st.form_submit_button("🔮 Predict Yield", use_container_width=True)
        
        if submitted:
            with st.spinner("Analyzing crop yield potential..."):
                # Simulate yield prediction
                import random
                time.sleep(2)
                
                # Mock prediction results
                base_yields = {
                    "wheat": 3000,
                    "rice": 4000,
                    "corn": 5000,
                    "soybeans": 2500,
                    "tomatoes": 40000
                }
                
                base_yield = base_yields[crop_type]
                weather_factor = random.uniform(0.8, 1.2)
                soil_factor = random.uniform(0.9, 1.1)
                predicted_yield = base_yield * field_size * weather_factor * soil_factor
                confidence = random.uniform(0.75, 0.95)
                
                st.success("✅ Yield prediction completed!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "🌾 Predicted Yield",
                        f"{predicted_yield:,.0f} kg",
                        f"{predicted_yield/field_size:,.0f} kg/ha"
                    )
                
                with col2:
                    st.metric(
                        "🎯 Confidence Score",
                        f"{confidence:.1%}",
                        "High confidence" if confidence > 0.85 else "Medium confidence"
                    )
                
                with col3:
                    st.metric(
                        "💰 Estimated Value",
                        f"${predicted_yield * 0.5:,.0f}",
                        "Market price estimate"
                    )
                
                # Factors analysis
                st.subheader("📊 Yield Factors Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🌤️ Weather Impact**")
                    weather_impact = "Positive" if weather_factor > 1.0 else "Negative"
                    st.write(f"• Impact: {weather_impact} ({weather_factor:.2f}x)")
                    st.write("• Temperature suitability: Good")
                    st.write("• Rainfall adequacy: Adequate")
                    st.write("• Growing season length: Optimal")
                
                with col2:
                    st.write("**🌍 Soil Impact**")
                    soil_impact = "Positive" if soil_factor > 1.0 else "Neutral"
                    st.write(f"• Impact: {soil_impact} ({soil_factor:.2f}x)")
                    st.write("• pH level: Suitable")
                    st.write("• Nutrient availability: Good")
                    st.write("• Drainage: Adequate")
                
                # Recommendations
                st.subheader("💡 Recommendations")
                recommendations = [
                    "Monitor soil moisture levels regularly during growing season",
                    "Apply balanced fertilizer based on soil test results",
                    "Consider pest management strategies for optimal yield",
                    "Plan harvest timing based on weather forecasts",
                    "Keep detailed records for future yield comparisons"
                ]
                
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")

def show_iot_sensors_tab():
    """Display IoT sensors monitoring interface"""
    st.header("📡 IoT Sensors Dashboard")
    
    st.info("""
    📢 **IoT Integration Feature**: Monitor your farm with real-time sensor data.
    
    **Supported Sensors:**
    - Soil moisture and temperature
    - Air temperature and humidity
    - Light intensity
    - pH and nutrient levels
    """)
    
    # Sensor registration
    with st.expander("➕ Register New Sensor"):
        with st.form("sensor_registration"):
            col1, col2 = st.columns(2)
            
            with col1:
                sensor_id = st.text_input("🆔 Sensor ID", placeholder="SENSOR_001")
                sensor_type = st.selectbox(
                    "📊 Sensor Type",
                    ["soil_moisture", "soil_temperature", "air_temperature", "air_humidity", "ph_level"]
                )
            
            with col2:
                location_name = st.text_input("📍 Location Name", placeholder="Field A - North Section")
                
            if st.form_submit_button("📡 Register Sensor"):
                st.success(f"✅ Sensor {sensor_id} registered successfully!")
    
    # Mock sensor data display
    st.subheader("📊 Current Sensor Readings")
    
    # Generate mock sensor data
    import random
    
    sensors = [
        {"id": "SOIL_001", "type": "Soil Moisture", "location": "Field A", "value": random.randint(40, 70), "unit": "%", "status": "optimal"},
        {"id": "TEMP_001", "type": "Air Temperature", "location": "Field A", "value": random.randint(18, 28), "unit": "°C", "status": "optimal"},
        {"id": "PH_001", "type": "Soil pH", "location": "Field B", "value": round(random.uniform(6.0, 7.5), 1), "unit": "pH", "status": "optimal"},
        {"id": "HUM_001", "type": "Air Humidity", "location": "Greenhouse", "value": random.randint(60, 80), "unit": "%", "status": "optimal"},
    ]
    
    # Display sensor cards
    cols = st.columns(2)
    for i, sensor in enumerate(sensors):
        with cols[i % 2]:
            status_color = "🟢" if sensor["status"] == "optimal" else "🟡"
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <h4>{status_color} {sensor['type']}</h4>
                <p><strong>ID:</strong> {sensor['id']}</p>
                <p><strong>Location:</strong> {sensor['location']}</p>
                <p><strong>Reading:</strong> {sensor['value']} {sensor['unit']}</p>
                <p><strong>Status:</strong> {sensor['status'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sensor trends
    st.subheader("📈 Sensor Trends")
    
    # Generate mock trend data
    import pandas as pd
    import plotly.express as px
    
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    soil_moisture = [45 + 10 * (i % 7) + random.randint(-5, 5) for i in range(30)]
    temperature = [20 + 5 * (i % 10) + random.randint(-2, 2) for i in range(30)]
    
    df = pd.DataFrame({
        'Date': dates,
        'Soil Moisture (%)': soil_moisture,
        'Temperature (°C)': temperature
    })
    
    # Plot trends
    fig_moisture = px.line(df, x='Date', y='Soil Moisture (%)', title='Soil Moisture Trend')
    st.plotly_chart(fig_moisture, use_container_width=True)
    
    fig_temp = px.line(df, x='Date', y='Temperature (°C)', title='Temperature Trend')
    st.plotly_chart(fig_temp, use_container_width=True)

def show_marketplace_tab():
    """Display marketplace interface"""
    st.header("🛒 Agricultural Marketplace")
    
    st.info("""
    📢 **Marketplace Feature**: Connect with suppliers and buyers in your area.
    
    **Categories:**
    - Seeds & Seedlings
    - Farm Equipment
    - Fertilizers & Nutrients
    - Fresh Produce
    """)
    
    # Marketplace tabs
    market_tab1, market_tab2, market_tab3 = st.tabs(["🔍 Browse", "📝 Create Listing", "📊 My Listings"])
    
    with market_tab1:
        st.subheader("🔍 Browse Marketplace")
        
        # Search and filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search", placeholder="Search products...")
        
        with col2:
            category = st.selectbox(
                "📂 Category",
                ["All", "Seeds", "Equipment", "Fertilizers", "Produce", "Services"]
            )
        
        with col3:
            sort_by = st.selectbox("📊 Sort by", ["Newest", "Price: Low to High", "Price: High to Low"])
        
        # Mock marketplace listings
        listings = [
            {
                "title": "Organic Tomato Seeds - High Yield",
                "price": "$25.99",
                "seller": "Green Valley Farm",
                "location": "California, USA",
                "category": "Seeds",
                "image": "🍅"
            },
            {
                "title": "John Deere Tractor - Model 5055E",
                "price": "$35,000",
                "seller": "Farm Equipment Co.",
                "location": "Iowa, USA",
                "category": "Equipment",
                "image": "🚜"
            },
            {
                "title": "Organic Compost - Premium Quality",
                "price": "$45.00",
                "seller": "Eco Fertilizers",
                "location": "Oregon, USA",
                "category": "Fertilizers",
                "image": "🌱"
            },
            {
                "title": "Fresh Organic Carrots",
                "price": "$3.50/kg",
                "seller": "Sunny Acres Farm",
                "location": "Vermont, USA",
                "category": "Produce",
                "image": "🥕"
            }
        ]
        
        # Display listings
        for listing in listings:
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{listing['image']}</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{listing['title']}**")
                    st.write(f"💰 Price: {listing['price']}")
                    st.write(f"👤 Seller: {listing['seller']}")
                    st.write(f"📍 Location: {listing['location']}")
                    st.write(f"📂 Category: {listing['category']}")
                    
                    if st.button(f"📞 Contact Seller", key=f"contact_{listing['title']}"):
                        st.success("Contact information sent to your email!")
                
                st.divider()
    
    with market_tab2:
        st.subheader("📝 Create New Listing")
        
        with st.form("create_listing"):
            col1, col2 = st.columns(2)
            
            with col1:
                listing_title = st.text_input("📝 Title", placeholder="Product or service title")
                listing_category = st.selectbox("📂 Category", ["Seeds", "Equipment", "Fertilizers", "Produce", "Services"])
                listing_price = st.number_input("💰 Price ($)", min_value=0.0, step=0.01)
            
            with col2:
                listing_quantity = st.number_input("📦 Quantity", min_value=1, value=1)
                listing_unit = st.selectbox("📏 Unit", ["piece", "kg", "ton", "bag", "hour"])
                listing_location = st.text_input("📍 Location", placeholder="City, State")
            
            listing_description = st.text_area("📄 Description", placeholder="Detailed description of your listing...")
            
            if st.form_submit_button("📤 Create Listing", use_container_width=True):
                st.success("✅ Listing created successfully!")
                st.balloons()
    
    with market_tab3:
        st.subheader("📊 My Listings")
        
        # Mock user listings
        user_listings = [
            {"title": "Organic Wheat Seeds", "status": "Active", "views": 45, "inquiries": 3},
            {"title": "Soil Testing Service", "status": "Active", "views": 23, "inquiries": 1},
            {"title": "Used Plow Equipment", "status": "Sold", "views": 67, "inquiries": 8}
        ]
        
        for listing in user_listings:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**{listing['title']}**")
            
            with col2:
                status_color = "🟢" if listing['status'] == "Active" else "🔴"
                st.write(f"{status_color} {listing['status']}")
            
            with col3:
                st.write(f"👁️ {listing['views']} views")
            
            with col4:
                st.write(f"📧 {listing['inquiries']} inquiries")

def show_community_tab():
    """Display community forum interface"""
    st.header("👥 Community Forum")
    
    st.info("""
    📢 **Community Feature**: Connect with fellow farmers, share knowledge, and get help.
    
    **Categories:**
    - Questions & Help
    - Tips & Tricks
    - Farm Showcase
    - Market Discussion
    """)
    
    # Community tabs
    comm_tab1, comm_tab2, comm_tab3 = st.tabs(["💬 Recent Posts", "✍️ Create Post", "🏆 My Activity"])
    
    with comm_tab1:
        st.subheader("💬 Recent Community Posts")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            post_category = st.selectbox("📂 Category", ["All", "Questions", "Tips", "Showcase", "Discussion"])
        
        with col2:
            sort_posts = st.selectbox("📊 Sort by", ["Newest", "Most Liked", "Most Replies"])
        
        # Mock community posts
        posts = [
            {
                "title": "Best practices for organic pest control?",
                "author": "FarmGuru123",
                "category": "Question",
                "replies": 12,
                "likes": 8,
                "time": "2 hours ago",
                "preview": "I'm transitioning to organic farming and looking for effective pest control methods..."
            },
            {
                "title": "Amazing tomato harvest this season!",
                "author": "TomatoKing",
                "category": "Showcase",
                "replies": 5,
                "likes": 23,
                "time": "4 hours ago",
                "preview": "Just wanted to share my excitement about this year's tomato crop..."
            },
            {
                "title": "Water-saving irrigation tip",
                "author": "EcoFarmer",
                "category": "Tip",
                "replies": 8,
                "likes": 15,
                "time": "1 day ago",
                "preview": "Here's a simple tip that reduced my water usage by 30%..."
            }
        ]
        
        # Display posts
        for post in posts:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{post['title']}**")
                    st.write(f"👤 By {post['author']} • 📂 {post['category']} • ⏰ {post['time']}")
                    st.write(post['preview'])
                
                with col2:
                    st.write(f"💬 {post['replies']}")
                    st.write(f"❤️ {post['likes']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👍 Like", key=f"like_{post['title']}"):
                        st.success("Liked!")
                with col2:
                    if st.button("💬 Reply", key=f"reply_{post['title']}"):
                        st.info("Reply feature coming soon!")
                with col3:
                    if st.button("📤 Share", key=f"share_{post['title']}"):
                        st.success("Shared!")
                
                st.divider()
    
    with comm_tab2:
        st.subheader("✍️ Create New Post")
        
        with st.form("create_post"):
            post_title = st.text_input("📝 Title", placeholder="What's your question or topic?")
            post_category = st.selectbox("📂 Category", ["Question", "Tip", "Showcase", "Discussion"])
            post_content = st.text_area("📄 Content", placeholder="Share your thoughts, questions, or experiences...", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                post_tags = st.text_input("🏷️ Tags", placeholder="organic, irrigation, pest-control (comma separated)")
            with col2:
                post_location = st.text_input("📍 Location (optional)", placeholder="Your farming location")
            
            if st.form_submit_button("📤 Create Post", use_container_width=True):
                st.success("✅ Post created successfully!")
                st.balloons()
    
    with comm_tab3:
        st.subheader("🏆 My Community Activity")
        
        # Mock user activity stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Posts Created", "12")
        
        with col2:
            st.metric("💬 Replies Given", "45")
        
        with col3:
            st.metric("❤️ Likes Received", "89")
        
        with col4:
            st.metric("🏆 Reputation Score", "156")
        
        st.subheader("📊 Recent Activity")
        
        activities = [
            "Posted: 'Soil pH testing methods' in Tips category",
            "Replied to: 'Best fertilizer for tomatoes?'",
            "Liked: 'Amazing corn harvest results'",
            "Posted: 'Need help with irrigation system' in Questions"
        ]
        
        for activity in activities:
            st.write(f"• {activity}")

def main():
    """Main application function"""
    # Show API status in sidebar
    show_api_status()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
    .guest-banner {
        background: linear-gradient(90deg, #FFA500, #FF6347);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add option for guest access
    if not st.session_state.authenticated:
        # Show guest access option
        st.markdown("""
        <div class="guest-banner">
            <h3>🌱 Welcome to AgriTech Assistant</h3>
            <p>Login for full features or continue as guest with limited access</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Login / Register", use_container_width=True):
                st.session_state.show_auth = True
        
        with col2:
            if st.button("👤 Continue as Guest", use_container_width=True):
                st.session_state.guest_mode = True
        
        # Show login page if requested
        if st.session_state.get('show_auth', False):
            show_login_page()
        elif st.session_state.get('guest_mode', False):
            show_dashboard()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()