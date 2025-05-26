module.exports = {
  name: 'agritech-assistant',
  version: '1.0.0',
  main: "node_modules/expo/AppEntry.js",
  extra: {
    eas: {
      projectId: 'agritech-assistant'
    }
  },
  orientation: 'portrait',
  icon: './assets/icon.png',
  userInterfaceStyle: 'light',
  splash: {
    image: './assets/splash.png',
    resizeMode: 'contain',
    backgroundColor: '#ffffff'
  },
  assetBundlePatterns: [
    '**/*'
  ],
  ios: {
    supportsTablet: true
  },
  android: {
    adaptiveIcon: {
      foregroundImage: './assets/adaptive-icon.png',
      backgroundColor: '#ffffff'
    }
  }
};