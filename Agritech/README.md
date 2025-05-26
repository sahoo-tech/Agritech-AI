# AgriTech Assistant

A mobile-first AI-powered agricultural assistance application that helps farmers identify crop diseases, get personalized farming advice, and access local weather and soil data.

## Key Features

- **Crop Disease Detection**: Uses computer vision and YOLOv8/MobileNet to identify plant diseases from leaf images
- **Multilingual AI Assistant**: NLP-powered chatbot that communicates in local languages
- **Geospatial Analysis**: Provides hyperlocal weather, soil, and pest data
- **Offline Support**: Works with limited or no internet connectivity

## Tech Stack

- **Frontend**: React Native with Expo
- **AI/ML**: TensorFlow.js for on-device inference
- **Location Services**: Expo Location
- **Storage**: AsyncStorage for offline data persistence
- **APIs**: Weather and soil data integration

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Run on your device:
- Scan the QR code with Expo Go (Android)
- Scan the QR code with Camera app (iOS)

## Project Structure

```
├── src/
│   ├── screens/
│   │   ├── HomeScreen.tsx         # Main navigation hub
│   │   ├── DiseaseDetectionScreen.tsx  # Camera and ML integration
│   │   ├── ChatbotScreen.tsx      # AI assistant interface
│   │   └── WeatherDataScreen.tsx  # Weather and soil data
│   └── components/                 # Reusable UI components
├── App.tsx                        # Root component
└── package.json                   # Dependencies
```