import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import * as Location from 'expo-location';
import axios from 'axios';

type WeatherData = {
  temperature: number;
  humidity: number;
  description: string;
  windSpeed: number;
};

type SoilData = {
  moisture: number;
  ph: number;
  nutrients: {
    nitrogen: number;
    phosphorus: number;
    potassium: number;
  };
};

export default function WeatherDataScreen() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [soilData, setSoilData] = useState<SoilData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        console.error('Location permission denied');
        return;
      }

      const location = await Location.getCurrentPositionAsync({});
      setLocation(location);

      // Simulated weather data (replace with actual API call)
      setWeatherData({
        temperature: 25,
        humidity: 65,
        description: 'Partly Cloudy',
        windSpeed: 10
      });

      // Simulated soil data (replace with actual API call)
      setSoilData({
        moisture: 35,
        ph: 6.5,
        nutrients: {
          nitrogen: 45,
          phosphorus: 30,
          potassium: 25
        }
      });
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2C3E50" />
        <Text style={styles.loadingText}>Loading data...</Text>
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {location && (
        <View style={styles.locationContainer}>
          <Text style={styles.locationText}>
            Location: {location.coords.latitude.toFixed(4)}, {location.coords.longitude.toFixed(4)}
          </Text>
        </View>
      )}

      {weatherData && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Weather Conditions</Text>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Temperature:</Text>
            <Text style={styles.value}>{weatherData.temperature}°C</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Humidity:</Text>
            <Text style={styles.value}>{weatherData.humidity}%</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Conditions:</Text>
            <Text style={styles.value}>{weatherData.description}</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Wind Speed:</Text>
            <Text style={styles.value}>{weatherData.windSpeed} km/h</Text>
          </View>
        </View>
      )}

      {soilData && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Soil Analysis</Text>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Soil Moisture:</Text>
            <Text style={styles.value}>{soilData.moisture}%</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Soil pH:</Text>
            <Text style={styles.value}>{soilData.ph}</Text>
          </View>
          <Text style={styles.subTitle}>Nutrient Levels</Text>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Nitrogen (N):</Text>
            <Text style={styles.value}>{soilData.nutrients.nitrogen} mg/kg</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Phosphorus (P):</Text>
            <Text style={styles.value}>{soilData.nutrients.phosphorus} mg/kg</Text>
          </View>
          <View style={styles.dataRow}>
            <Text style={styles.label}>Potassium (K):</Text>
            <Text style={styles.value}>{soilData.nutrients.potassium} mg/kg</Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    padding: 15
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#2C3E50'
  },
  locationContainer: {
    backgroundColor: '#FFFFFF',
    padding: 10,
    borderRadius: 10,
    marginBottom: 15
  },
  locationText: {
    fontSize: 14,
    color: '#7F8C8D',
    textAlign: 'center'
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2C3E50',
    marginBottom: 15
  },
  subTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2C3E50',
    marginTop: 10,
    marginBottom: 10
  },
  dataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  label: {
    fontSize: 16,
    color: '#7F8C8D'
  },
  value: {
    fontSize: 16,
    color: '#2C3E50',
    fontWeight: '500'
  }
});