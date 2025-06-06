#!/usr/bin/env python3
"""
AgriTech Assistant - Simple Demo Frontend
Quick demo without authentication requirements
"""

import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import json
from datetime import datetime

# Configuration
BASE_API_URL = "http://localhost:8000/api"
WEATHER_API_URL = f"{BASE_API_URL}/weather"

# Page configuration
st.set_page_config(
    page_title="🌱 AgriTech Assistant Demo",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_weather_data(latitude: float, longitude: float):
    """Get weather data from public API"""
    try:
        data = {"latitude": latitude, "longitude": longitude}
        response = requests.post(f"{WEATHER_API_URL}/public/current", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Weather API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return None

def get_soil_data(latitude: float, longitude: float):
    """Get soil data from public API"""
    try:
        data = {"latitude": latitude, "longitude": longitude}
        response = requests.post(f"{WEATHER_API_URL}/public/soil", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Soil API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error fetching soil data: {str(e)}")
        return None

def animated_seed_planting():
    """Show animated seed planting"""
    st.markdown("### 🌱 Seed Planting Animation")
    planting_placeholder = st.empty()
    stages = ["🌱", "🌿", "🌾", "🌻", "🌽"]
    
    for stage in stages:
        planting_placeholder.markdown(
            f"<h1 style='text-align:center; font-size:4rem;'>{stage}</h1>", 
            unsafe_allow_html=True
        )
        time.sleep(0.8)
    
    planting_placeholder.markdown(
        "<h1 style='text-align:center; color:green;'>🌻 Crop Grown Successfully!</h1>", 
        unsafe_allow_html=True
    )

def main():
    """Main application function"""
    
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
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🌱 AgriTech Assistant Demo</h1>', unsafe_allow_html=True)
    st.markdown("### Your AI-powered agricultural companion")
    
    # Sidebar
    with st.sidebar:
        st.title("🌱 Demo Settings")
        
        st.markdown("---")
        
        # Location input
        st.subheader("📍 Location Settings")
        latitude = st.number_input("Latitude", value=20.5937, format="%.4f")
        longitude = st.number_input("Longitude", value=78.9629, format="%.4f")
        
        # Predefined locations
        st.subheader("🗺️ Quick Locations")
        if st.button("🇮🇳 Delhi, India"):
            latitude, longitude = 28.6139, 77.2090
            st.rerun()
        if st.button("🇺🇸 Iowa, USA"):
            latitude, longitude = 41.8781, -93.0977
            st.rerun()
        if st.button("🇧🇷 São Paulo, Brazil"):
            latitude, longitude = -23.5505, -46.6333
            st.rerun()
        
        st.markdown("---")
        st.info("💡 This is a demo version. Full features available after registration!")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🌤️ Weather & Soil", "🗺️ Farm Map", "📊 Analytics", "🎮 Demo Features"])
    
    with tab1:
        st.header("🌤️ Current Weather & Soil Conditions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Get Weather Data", type="primary"):
                with st.spinner("Fetching weather data..."):
                    weather_data = get_weather_data(latitude, longitude)
                    if weather_data:
                        st.session_state.weather_data = weather_data
                        st.success("Weather data updated!")
        
        with col2:
            if st.button("🔄 Get Soil Data", type="primary"):
                with st.spinner("Fetching soil data..."):
                    soil_data = get_soil_data(latitude, longitude)
                    if soil_data:
                        st.session_state.soil_data = soil_data
                        st.success("Soil data updated!")
        
        # Display weather data
        if hasattr(st.session_state, 'weather_data') and st.session_state.weather_data:
            weather = st.session_state.weather_data
            
            st.subheader("🌡️ Current Weather")
            
            # Weather metrics
            col1, col2, col3, col4 = st.columns(4)
            
            current = weather.get('current', {})
            with col1:
                temp = current.get('temperature', 'N/A')
                st.metric("Temperature", f"{temp}°C" if temp != 'N/A' else temp)
            
            with col2:
                humidity = current.get('humidity', 'N/A')
                st.metric("Humidity", f"{humidity}%" if humidity != 'N/A' else humidity)
            
            with col3:
                wind = current.get('wind_speed', 'N/A')
                st.metric("Wind Speed", f"{wind} km/h" if wind != 'N/A' else wind)
            
            with col4:
                pressure = current.get('pressure', 'N/A')
                st.metric("Pressure", f"{pressure} hPa" if pressure != 'N/A' else pressure)
            
            # Weather condition
            condition = current.get('condition', 'Unknown')
            description = current.get('description', '')
            st.markdown(f"**Condition:** {condition} - {description}")
            
            # Agricultural conditions
            if weather.get('agricultural_conditions'):
                st.subheader("🌱 Agricultural Conditions")
                ag_conditions = weather['agricultural_conditions']
                
                col1, col2 = st.columns(2)
                with col1:
                    planting = ag_conditions.get('planting_suitability', 'Unknown')
                    st.markdown(f"**Planting Suitability:** {planting}")
                
                with col2:
                    irrigation = ag_conditions.get('irrigation_need', 'Unknown')
                    st.markdown(f"**Irrigation Need:** {irrigation}")
            
            # Weather alerts
            if weather.get('alerts'):
                st.subheader("⚠️ Weather Alerts")
                for alert in weather['alerts']:
                    alert_type = alert.get('type', 'Alert')
                    alert_msg = alert.get('message', 'No details available')
                    st.warning(f"**{alert_type}:** {alert_msg}")
        
        # Display soil data
        if hasattr(st.session_state, 'soil_data') and st.session_state.soil_data:
            soil = st.session_state.soil_data
            
            st.subheader("🌍 Soil Analysis")
            
            # Soil metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                moisture = soil.get('moisture_content', soil.get('moisture', 'N/A'))
                st.metric("Soil Moisture", f"{moisture}%" if moisture != 'N/A' else moisture)
            
            with col2:
                ph = soil.get('ph_level', 'N/A')
                st.metric("pH Level", f"{ph}" if ph != 'N/A' else ph)
            
            with col3:
                soil_temp = soil.get('temperature', 'N/A')
                st.metric("Soil Temperature", f"{soil_temp}°C" if soil_temp != 'N/A' else soil_temp)
            
            # Soil type and characteristics
            soil_type = soil.get('soil_type', 'Unknown')
            st.markdown(f"**Soil Type:** {soil_type}")
            
            # Nutrients
            if soil.get('nutrients'):
                st.subheader("🧪 Soil Nutrients")
                nutrients = soil['nutrients']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    nitrogen = nutrients.get('nitrogen', 'N/A')
                    st.metric("Nitrogen (N)", f"{nitrogen}" if nitrogen != 'N/A' else nitrogen)
                
                with col2:
                    phosphorus = nutrients.get('phosphorus', 'N/A')
                    st.metric("Phosphorus (P)", f"{phosphorus}" if phosphorus != 'N/A' else phosphorus)
                
                with col3:
                    potassium = nutrients.get('potassium', 'N/A')
                    st.metric("Potassium (K)", f"{potassium}" if potassium != 'N/A' else potassium)
            
            # Recommendations
            if soil.get('recommendations'):
                st.subheader("💡 Soil Recommendations")
                for i, rec in enumerate(soil['recommendations'], 1):
                    st.markdown(f"{i}. {rec}")
    
    with tab2:
        st.header("🗺️ Farm Location Map")
        
        # Create map
        m = folium.Map(location=[latitude, longitude], zoom_start=10)
        
        # Add marker for farm location
        folium.Marker(
            [latitude, longitude],
            popup=f"Farm Location\nLat: {latitude:.4f}\nLon: {longitude:.4f}",
            tooltip="Click for details",
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(m)
        
        # Display map
        st_folium(m, width=700, height=500)
        
        # Location info
        st.subheader("📍 Location Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Latitude:** {latitude:.6f}")
            st.write(f"**Longitude:** {longitude:.6f}")
        
        with col2:
            # You could add reverse geocoding here
            st.write("**Region:** Agricultural Zone")
            st.write("**Climate:** Varies by season")
    
    with tab3:
        st.header("📊 Agricultural Analytics")
        
        # Sample analytics data
        if st.button("📈 Generate Sample Analytics"):
            # Create sample data for demonstration
            dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
            
            # Temperature trend
            temp_data = pd.DataFrame({
                'Date': dates,
                'Temperature': [20 + 5 * (i % 7) + (i % 3) for i in range(len(dates))]
            })
            
            fig_temp = px.line(temp_data, x='Date', y='Temperature', 
                              title='Temperature Trend (Sample Data)')
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # Humidity trend
            humidity_data = pd.DataFrame({
                'Date': dates,
                'Humidity': [60 + 20 * (i % 5) + (i % 2) for i in range(len(dates))]
            })
            
            fig_humidity = px.line(humidity_data, x='Date', y='Humidity', 
                                  title='Humidity Trend (Sample Data)')
            st.plotly_chart(fig_humidity, use_container_width=True)
            
            # Crop recommendations
            st.subheader("🌾 Recommended Crops for Current Conditions")
            crops = ["Wheat", "Rice", "Corn", "Soybeans", "Tomatoes"]
            suitability = [85, 70, 90, 75, 80]
            
            crop_df = pd.DataFrame({
                'Crop': crops,
                'Suitability (%)': suitability
            })
            
            fig_crops = px.bar(crop_df, x='Crop', y='Suitability (%)', 
                              title='Crop Suitability Analysis')
            st.plotly_chart(fig_crops, use_container_width=True)
    
    with tab4:
        st.header("🎮 Interactive Demo Features")
        
        # Animated seed planting
        if st.button("🌱 Start Seed Planting Animation"):
            animated_seed_planting()
        
        st.markdown("---")
        
        # Sample disease detection
        st.subheader("🔍 Disease Detection Demo")
        st.info("Upload a plant image to analyze for diseases (Feature available in full version)")
        
        uploaded_file = st.file_uploader(
            "Choose a plant image...",
            type=['png', 'jpg', 'jpeg'],
            help="This is a demo - actual analysis requires authentication"
        )
        
        if uploaded_file is not None:
            from PIL import Image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            if st.button("🔍 Analyze (Demo)"):
                with st.spinner("Analyzing image..."):
                    time.sleep(2)  # Simulate processing
                    st.success("Demo Analysis Complete!")
                    st.markdown("""
                    **Demo Results:**
                    - Plant appears healthy ✅
                    - No diseases detected
                    - Recommended action: Continue regular care
                    
                    *Note: This is a demo result. Real analysis available in full version.*
                    """)
        
        st.markdown("---")
        
        # AI Chat Demo
        st.subheader("💬 AI Assistant Demo")
        st.info("Ask agricultural questions (Feature available in full version)")
        
        user_question = st.text_input("Ask a farming question:")
        if user_question and st.button("Ask AI"):
            with st.spinner("AI is thinking..."):
                time.sleep(1)
                st.markdown("""
                **AI Response (Demo):**
                
                Thank you for your question about farming! In the full version of AgriTech Assistant, 
                I can provide detailed, personalized advice about:
                
                - Crop selection and planting times
                - Disease identification and treatment
                - Soil management and fertilization
                - Weather-based farming decisions
                - Market insights and pricing
                
                Please register for the full experience!
                """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🌱 AgriTech Assistant Demo | Built with ❤️ for farmers worldwide</p>
        <p>Register for full features including AI chat, disease detection, and personalized recommendations!</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()