// Create a new file: src/config/api.js (or wherever your API calls are)

// Production URL
const API_BASE_URL = 'https://nexus-bjg6.onrender.com/research';

export const apiClient = {
  // Send message to chat
  sendMessage: async (message) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to send message');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // Create new chat
  createNewChat: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to create chat');
      return await response.json();
    } catch (error) {
      console.error('Error creating chat:', error);
      throw error;
    }
  },

  // Get chat history
  getChatHistory: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/history`);
      if (!response.ok) throw new Error('Failed to get history');
      return await response.json();
    } catch (error) {
      console.error('Error getting history:', error);
      throw error;
    }
  },

  // Get connectors
  getConnectors: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/connectors`);
      if (!response.ok) throw new Error('Failed to get connectors');
      return await response.json();
    } catch (error) {
      console.error('Error getting connectors:', error);
      throw error;
    }
  },

  // Connect a service
  connectService: async (connectorId, credentials) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/connectors/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ connectorId, credentials }),
      });

      if (!response.ok) throw new Error('Failed to connect service');
      return await response.json();
    } catch (error) {
      console.error('Error connecting service:', error);
      throw error;
    }
  },

  // Get plugins
  getPlugins: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/plugins`);
      if (!response.ok) throw new Error('Failed to get plugins');
      return await response.json();
    } catch (error) {
      console.error('Error getting plugins:', error);
      throw error;
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      return await response.json();
    } catch (error) {
      console.error('Backend is not available:', error);
      return { status: 'offline' };
    }
  }
};

export default apiClient;
