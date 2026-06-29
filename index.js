import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ==================== CORS CONFIGURATION ====================
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'https://nexus-5wf8crw95-krishnadev2.vercel.app'
    ];

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  optionsSuccessStatus: 200
};

// ==================== MIDDLEWARE ====================
app.use(cors(corsOptions));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));
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
app.post("/api/chat/send", async (req, res) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ 
        success: false, 
        error: 'Message is required' 
      });
    }

    const response = await fetch("https://nexus-bjg6.onrender.com/research", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: message,
        target_url: "",
        custom_instructions: "",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json({
      success: true,
      reply: data.report_html,
    });
  } catch (error) {
    console.error('Error in /api/chat/send:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// 3. GET CHAT HISTORY
app.get('/api/chat/history', (req, res) => {
  try {
    res.json({
      success: true,
      history: []
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
      plugins: []
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
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, "../public/index.html")).catch(() => {
    res.status(404).json({ error: 'Not found' });
  });
});

// ==================== START SERVER ====================
const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, () => {
  console.log(`✓ Nexus AI Backend running on port ${PORT}`);
  console.log(`✓ CORS enabled for: https://nexus-5wf8crw95-krishnadev2.vercel.app`);
  console.log(`✓ Server ready to accept requests`);
});

server.on('error', (err) => {
  console.error('❌ Server error:', err);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});
