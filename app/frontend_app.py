import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium
import time

# Backend API endpoints (adjust base URL as needed)
BASE_API_URL = "http://localhost:8000/api/weather"

def get_location():
    # For demo, use fixed coordinates; in real app, get from user input or geolocation
    return {"latitude": 20.5937, "longitude": 78.9629}

def get_weather(location):
    try:
        response = requests.post(f"{BASE_API_URL}/current", json=location)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Weather API error: {response.status_code} {response.text}")
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
    return None

def get_soil_health(location):
    try:
        response = requests.post(f"{BASE_API_URL}/soil", json=location)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Soil API error: {response.status_code} {response.text}")
    except Exception as e:
        st.error(f"Error fetching soil data: {e}")
    return None

def get_crop_recommendations():
    st.info("Crop recommendations are currently unavailable.")
    return None

def get_market_prices():
    st.info("Market price data is currently unavailable.")
    return None

def animated_seed_planting():
    st.markdown("### 🌱 Seed Planting Animation")
    planting_placeholder = st.empty()
    stages = [
        "🌱", "🌿", "🌾", "🌻", "🌽"
    ]
    for stage in stages:
        planting_placeholder.markdown(f"<h1 style='text-align:center'>{stage}</h1>", unsafe_allow_html=True)
        time.sleep(0.8)
    planting_placeholder.markdown("<h1 style='text-align:center'>🌻 Crop Grown!</h1>", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Agritech Farmer Dashboard", layout="wide")
    st.title("🌾 Agritech Farmer Dashboard")

    location = get_location()

    # Weather Section
    st.header("Current Weather and Forecast")
    weather = get_weather(location)
    if weather:
        st.write(f"Location: {weather.get('location', 'Unknown')}")
        st.write(f"Temperature: {weather.get('temperature', 'N/A')} °C")
        st.write(f"Condition: {weather.get('condition', 'N/A')}")
        st.write(f"Humidity: {weather.get('humidity', 'N/A')}%")
    else:
        st.info("Weather data not available.")

    # Soil Health Section
    st.header("Soil Health and Moisture")
    soil = get_soil_health(location)
    if soil:
        st.write(f"Soil Moisture: {soil.get('moisture', 'N/A')}%")
        st.write(f"Soil pH: {soil.get('ph_level', 'N/A')}")
        st.write(f"Soil Temperature: {soil.get('temperature', 'N/A')} °C")
    else:
        st.info("Soil data not available.")

    # Crop Recommendations Section
    st.header("Crop Recommendations")
    recommendations = get_crop_recommendations()
    if recommendations and "crops" in recommendations:
        st.write(", ".join(recommendations["crops"]))
    else:
        st.info("Crop recommendations not available.")

    # Market Prices Section
    st.header("Market Price Trends")
    market_data = get_market_prices()
    if market_data and "prices" in market_data:
        df = pd.DataFrame(market_data["prices"])
        fig = px.line(df, x="date", y="price", color="commodity", title="Market Price Trends")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Market price data not available.")

    # Animated Farm Plot Viewer
    st.header("Farm Plot Viewer")
    m = folium.Map(location=[location["latitude"], location["longitude"]], zoom_start=5)  # Centered on location
    folium.Marker([location["latitude"], location["longitude"]], popup="Farm Center").add_to(m)
    st_folium(m, width=700, height=450)

    # Gamified UX: Seed Planting Animation
    animated_seed_planting()

if __name__ == "__main__":
    main()
