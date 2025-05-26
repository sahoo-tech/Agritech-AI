import React from 'react';
import { StyleSheet, View, TouchableOpacity, Text, SafeAreaView, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';

type FeatureCard = {
  title: string;
  description: string;
  screen: string;
  icon: string;
};

const features: FeatureCard[] = [
  {
    title: 'Disease Detection',
    description: 'Scan plant leaves to identify diseases',
    screen: 'DiseaseDetection',
    icon: '🔍'
  },
  {
    title: 'AI Assistant',
    description: 'Chat with our multilingual farming expert',
    screen: 'Chatbot',
    icon: '💬'
  },
  {
    title: 'Weather & Soil',
    description: 'Get local weather and soil conditions',
    screen: 'WeatherData',
    icon: '🌤️'
  }
];

export default function HomeScreen() {
  const navigation = useNavigation<StackNavigationProp<any>>();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>Welcome to AgriTech</Text>
          <Text style={styles.subtitle}>Your Smart Farming Assistant</Text>
        </View>
        
        <View style={styles.cardsContainer}>
          {features.map((feature, index) => (
            <TouchableOpacity
              key={index}
              style={styles.card}
              onPress={() => navigation.navigate(feature.screen)}
            >
              <Text style={styles.cardIcon}>{feature.icon}</Text>
              <Text style={styles.cardTitle}>{feature.title}</Text>
              <Text style={styles.cardDescription}>{feature.description}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5'
  },
  header: {
    padding: 20,
    alignItems: 'center'
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2C3E50'
  },
  subtitle: {
    fontSize: 16,
    color: '#7F8C8D',
    marginTop: 5
  },
  cardsContainer: {
    padding: 15
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  cardIcon: {
    fontSize: 32,
    marginBottom: 10
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2C3E50',
    marginBottom: 5
  },
  cardDescription: {
    fontSize: 14,
    color: '#7F8C8D'
  }
});