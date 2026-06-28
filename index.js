import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// ==================== API ROUTES ====================

// 1. NEW CHAT - Create new chat session
app.post('/api/chat/new', (req, res) => {
  try {
    const chatId = `chat_${Date.now()}`;
    res.json({
      success: true,
      chatId: chatId,
      message: 'New chat created',
      createdAt: new Date()
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 2. SEND MESSAGE - Handle chat messages
app.post('/api/chat/message', async (req, res) => {
  try {
    const response = await fetch('https://nexus-bjg6.onrender.com/api/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    res.json(data);

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});
// 3. GET CHAT HISTORY
app.get('/api/chat/history', (req, res) => {
  try {
    res.json({
      success: true,
      history: [
        // TODO: Load from database
      ]
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 4. CONNECTORS - Get available connectors
app.get('/api/connectors', (req, res) => {
  try {
    res.json({
      success: true,
      connectors: [
        { id: 1, name: 'GitHub', icon: 'github', connected: false },
        { id: 2, name: 'Jira', icon: 'jira', connected: false },
        { id: 3, name: 'Slack', icon: 'slack', connected: false },
        { id: 4, name: 'Gmail', icon: 'gmail', connected: false }
      ]
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 5. CONNECT - Connect a service
app.post('/api/connectors/connect', (req, res) => {
  try {
    const { connectorId, credentials } = req.body;
    
    // TODO: Implement OAuth or API key authentication
    res.json({
      success: true,
      message: 'Connector connected successfully',
      connectorId: connectorId
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 6. CUSTOM PLUGINS - Save custom plugin
app.post('/api/plugins/custom', (req, res) => {
  try {
    const { toolName, endpoint } = req.body;

    if (!toolName || !endpoint) {
      return res.status(400).json({ 
        success: false, 
        error: 'Tool name and endpoint URL are required' 
      });
    }

    const pluginId = `plugin_${Date.now()}`;
    res.json({
      success: true,
      pluginId: pluginId,
      toolName: toolName,
      endpoint: endpoint,
      createdAt: new Date()
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 7. GET PLUGINS
app.get('/api/plugins', (req, res) => {
  try {
    res.json({
      success: true,
      plugins: [
        // TODO: Load from database
      ]
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 8. INSTRUCTIONS PAGE DATA
app.get('/api/instructions', (req, res) => {
  try {
    res.json({
      success: true,
      title: 'How to Use Nexus AI',
      content: 'Add your instructions content here'
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 9. PRIVACY POLICY DATA
app.get('/api/privacy', (req, res) => {
  try {
    res.json({
      success: true,
      title: 'Privacy Policy',
      content: 'Add your privacy policy content here'
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 10. Health Check
app.get('/api/health', (req, res) => {
  res.json({ status: 'Backend is running!' });
});

// ==================== SERVE FRONTEND ====================
// Catch-all for frontend routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// ==================== START SERVER ====================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✓ Nexus AI Backend running on port ${PORT}`);
});

export default app;
