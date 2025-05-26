import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StyleSheet, View } from 'react-native';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import DiseaseDetectionScreen from './src/screens/DiseaseDetectionScreen';
import ChatbotScreen from './src/screens/ChatbotScreen';
import WeatherDataScreen from './src/screens/WeatherDataScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ title: 'AgriTech Assistant' }}
        />
        <Stack.Screen 
          name="DiseaseDetection" 
          component={DiseaseDetectionScreen} 
          options={{ title: 'Disease Detection' }}
        />
        <Stack.Screen 
          name="Chatbot" 
          component={ChatbotScreen} 
          options={{ title: 'AI Assistant' }}
        />
        <Stack.Screen 
          name="WeatherData" 
          component={WeatherDataScreen} 
          options={{ title: 'Weather & Soil Data' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
});