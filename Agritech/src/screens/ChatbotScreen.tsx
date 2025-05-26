import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
};

export default function ChatbotScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadPreviousMessages();
  }, []);

  const loadPreviousMessages = async () => {
    try {
      const savedMessages = await AsyncStorage.getItem('chatMessages');
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages));
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const saveMessages = async (newMessages: Message[]) => {
    try {
      await AsyncStorage.setItem('chatMessages', JSON.stringify(newMessages));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);
    saveMessages(updatedMessages);
    setInputText('');
    setIsLoading(true);

    try {
      // Here we would integrate with OpenAI/ChatGPT API
      // For now, we'll simulate a response
      setTimeout(() => {
        const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: 'This is a simulated response. In the actual app, this would be an AI-generated response in the user\'s preferred language.',
          sender: 'bot',
          timestamp: new Date()
        };

        const messagesWithResponse = [...updatedMessages, botResponse];
        setMessages(messagesWithResponse);
        saveMessages(messagesWithResponse);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Error getting bot response:', error);
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView style={styles.messagesContainer}>
        {messages.map((message) => (
          <View 
            key={message.id}
            style={[
              styles.messageBox,
              message.sender === 'user' ? styles.userMessage : styles.botMessage
            ]}
          >
            <Text style={styles.messageText}>{message.text}</Text>
            <Text style={styles.timestamp}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </Text>
          </View>
        ))}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <Text>AI is thinking...</Text>
          </View>
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type your question..."
          multiline
        />
        <TouchableOpacity 
          style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!inputText.trim()}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5'
  },
  messagesContainer: {
    flex: 1,
    padding: 15
  },
  messageBox: {
    maxWidth: '80%',
    padding: 10,
    borderRadius: 10,
    marginBottom: 10
  },
  userMessage: {
    backgroundColor: '#2C3E50',
    alignSelf: 'flex-end'
  },
  botMessage: {
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start'
  },
  messageText: {
    color: '#FFFFFF',
    fontSize: 16
  },
  timestamp: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.7,
    marginTop: 5
  },
  loadingContainer: {
    padding: 10,
    alignItems: 'center'
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0'
  },
  input: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    fontSize: 16
  },
  sendButton: {
    backgroundColor: '#2C3E50',
    borderRadius: 20,
    paddingHorizontal: 20,
    justifyContent: 'center'
  },
  sendButtonDisabled: {
    backgroundColor: '#CCCCCC'
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold'
  }
});