import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Image } from 'react-native';
import { Camera, CameraType } from 'expo-camera';
import * as tf from '@tensorflow/tfjs';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function DiseaseDetectionScreen() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const cameraRef = React.useRef<Camera>(null);
  const [image, setImage] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<string | null>(null);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');

      const locPermission = await Location.requestForegroundPermissionsAsync();
      if (locPermission.status === 'granted') {
        const location = await Location.getCurrentPositionAsync({});
        setLocation(location);
      }

      await tf.ready();
      // Model loading would go here
    })();
  }, []);

  const takePicture = async () => {
    if (cameraRef.current) {
      const photo = await cameraRef.current.takePictureAsync();
      setImage(photo.uri);
      analyzePicture(photo.uri);
    }
  };

  const analyzePicture = async (imageUri: string) => {
    try {
      // Here we would:
      // 1. Load and preprocess the image
      // 2. Run it through the ML model
      // 3. Get predictions
      // For now, we'll just set a placeholder
      setPrediction('Analyzing image...');
      
      // Save data locally
      await AsyncStorage.setItem('lastScan', JSON.stringify({
        image: imageUri,
        location,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error analyzing picture:', error);
      setPrediction('Error analyzing image');
    }
  };

  if (hasPermission === null) {
    return <View style={styles.container}><Text>Requesting camera permission...</Text></View>;
  }
  if (hasPermission === false) {
    return <View style={styles.container}><Text>No access to camera</Text></View>;
  }

  return (
    <View style={styles.container}>
      {!image ? (
        <Camera
          style={styles.camera}
          type={CameraType.back}
          ref={cameraRef}
        >
          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.button} onPress={takePicture}>
              <Text style={styles.buttonText}>Take Picture</Text>
            </TouchableOpacity>
          </View>
        </Camera>
      ) : (
        <View style={styles.resultContainer}>
          <Image source={{ uri: image }} style={styles.previewImage} />
          {prediction && (
            <View style={styles.predictionContainer}>
              <Text style={styles.predictionText}>{prediction}</Text>
            </View>
          )}
          <TouchableOpacity 
            style={styles.button}
            onPress={() => setImage(null)}
          >
            <Text style={styles.buttonText}>Take Another Picture</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5'
  },
  camera: {
    flex: 1
  },
  buttonContainer: {
    flex: 1,
    backgroundColor: 'transparent',
    flexDirection: 'row',
    justifyContent: 'center',
    margin: 20,
    position: 'absolute',
    bottom: 0,
    width: '100%'
  },
  button: {
    backgroundColor: '#2C3E50',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    width: '80%'
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold'
  },
  resultContainer: {
    flex: 1,
    alignItems: 'center',
    padding: 20
  },
  previewImage: {
    width: '100%',
    height: 300,
    borderRadius: 10,
    marginBottom: 20
  },
  predictionContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    width: '100%'
  },
  predictionText: {
    fontSize: 16,
    textAlign: 'center'
  }
});