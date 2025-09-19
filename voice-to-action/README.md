# Voice Agent - Intelligent Voice Assistant with Browser Automation

A sophisticated voice-controlled AI assistant that seamlessly integrates conversational AI with browser automation. Built with a hybrid Swift + Python architecture for optimal performance and user experience.

## 🎯 **What We're Building**

An intelligent voice assistant that:
- **Responds to questions** like "What is machine learning?" using conversational AI
- **Performs web actions** like "Go to Google and search for weather" using browser automation
- **Automatically decides** which type of response is needed based on your request
- **Works seamlessly with Wispr Flow** for speech-to-text transcription
- **Provides a minimal, Siri-like interface** that stays out of your way

## 🚀 **How It Works**

1. **Press and hold Option key** → Minimal interface appears at top of screen
2. **Speak your request** → Wispr Flow transcribes speech to text
3. **Release Option key** → AI decides whether to respond conversationally or use browser
4. **Get your answer** → Either direct text response or automated web actions
5. **Focus returns** → Back to whatever you were doing

## 🏗️ **Architecture Overview**

### **Swift macOS App** (Frontend & System Integration)
- 🎨 **Minimal Siri-like UI** - Clean capsule interface with colorful gradient icon
- 🔑 **Global Option Key Detection** - Instant activation without interrupting workflow
- 🖥️ **Smart Focus Management** - Seamlessly switches between apps
- ⚡ **Native macOS Performance** - Lightning-fast response times
- 🎯 **Wispr Flow Integration** - Works perfectly with speech-to-text transcription

### **Python Backend** (AI Brain & Automation Engine)
- 🧠 **Dual Agent System** - LangChain for conversation + browser-use for automation
- 🤖 **Intelligent Routing** - Automatically decides which agent to use
- 🌐 **Browser Automation** - Full web interaction capabilities via Playwright
- 📡 **FastAPI Server** - High-performance REST API
- 🔄 **Session Management** - Maintains context and conversation history

## 🚀 **Quick Start**

### **1. Start Python Backend**
```bash
cd python_backend
./start_server.sh
```

### **2. Start Swift App**
```bash
cd VoiceBrowserAgent.swiftpm
swift run
```
- Grant accessibility permissions when prompted
- App window appears at top-center of screen

### **3. Usage**
1. **Press Option key down** → Minimal interface activates at top of screen
2. **Speak your request** → Wispr Flow transcribes speech to text field
3. **Release Option key** → AI processes and responds (conversation or browser action)
4. **Alternative:** Wait 3 seconds after speaking for auto-execution
5. **Click `?` button** → View instructions and examples

## 📋 **Setup Instructions**

### **Python Backend Setup**
```bash
cd python_backend

# Set OpenAI API key
export OPENAI_API_KEY='your-api-key-here'

# Install dependencies and start server
./start_server.sh
```

### **Swift App Setup**
1. Run `swift run` from the VoiceBrowserAgent.swiftpm directory
2. Grant **Accessibility** permissions when prompted:
   - System Preferences > Security & Privacy > Privacy > Accessibility
   - Enable VoiceBrowserAgent to monitor Option key globally

## 🔗 **Communication Flow**

```
1. Option Key Press → Swift App Activates
2. Wispr Flow → Text Input
3. Option Key Release → HTTP POST /execute
4. Python Backend → Analyzes Request Intent
5. Route Decision:
   ├── Conversational AI (LangChain) → Direct Response
   └── Browser Automation (browser-use) → Web Actions
6. Response → Swift App → User
7. Focus Restoration → Previous App
```

## 📁 **Project Structure**

```
voice-to-action/
├── README.md                          # This documentation
├── VoiceBrowserAgent.swiftpm/         # Swift Package (macOS App)
│   ├── Package.swift                 # Swift Package configuration
│   └── Sources/                      # Swift source files
│       ├── main.swift                # App entry point & window setup
│       ├── AppDelegate.swift         # App lifecycle & permissions
│       ├── AppState.swift            # Option key monitoring & state
│       ├── ContentView.swift         # Minimal Siri-like UI
│       ├── SettingsView.swift        # Settings interface
│       └── BackendService.swift      # HTTP client for Python API
└── python_backend/                   # Python AI Backend
    ├── browser_agent_api.py          # Dual-agent FastAPI server
    ├── requirements.txt              # Python dependencies
    ├── start_server.sh               # Auto-setup & start script
    ├── .env                          # OpenAI API key
    └── .venv/                        # Virtual environment
```

## 🎯 **Key Benefits of Hybrid Architecture**

### **Swift Side Advantages:**
- ⚡ **Lightning-fast** window switching (no subprocess calls)
- 🍎 **Native macOS experience** with proper focus management
- 🔑 **Reliable global hotkeys** using KeyboardShortcuts framework
- 🎨 **Beautiful SwiftUI interface** with smooth animations
- 📡 **System integration** that "just works"

### **Python Side Advantages:**
- 🤖 **Proven browser-use integration** (no porting needed)
- 🔧 **Rich Python ecosystem** for AI/LLM tasks
- 📚 **Easy to modify and extend** browser automation logic
- 🧪 **Simple to test and debug** backend functionality

## 🛠️ **API Endpoints**

### **Health Check**
```http
GET http://localhost:8000/health
```

### **Execute Command**
```http
POST http://localhost:8000/execute
Content-Type: application/json

{
    "command": "Go to Google and search for OpenAI",
    "headless": false
}
```

## 🔧 **Configuration**

### **Environment Variables** (python_backend/.env)
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### **Swift App Settings**
- Keyboard shortcuts (customizable via Settings)
- Backend URL configuration
- Auto-execute delay settings

## 🧪 **Testing**

### **Test Backend Only**
```bash
cd python_backend
source .venv/bin/activate
python browser_agent_api.py

# In another terminal
curl http://localhost:8000/health
```

### **Test Full Integration**
1. Start Python backend
2. Run Swift app
3. Press Option key → App should activate
4. Type "go to google" → Release Option → Should execute

## 🚨 **Troubleshooting**

### **Backend Issues**
- **"LLM not initialized"**: Check OPENAI_API_KEY is set
- **"Connection refused"**: Ensure backend is running on port 8000
- **"Module not found"**: Run `pip install -r requirements.txt`

### **Swift App Issues**
- **Option key not working**: Grant Accessibility permissions
- **App won't activate**: Grant Automation permissions  
- **Build errors**: Ensure Xcode 15+ and macOS 14+

### **Integration Issues**
- **"Backend not running"**: Start Python server first
- **Commands not executing**: Check backend logs for errors
- **Focus not restoring**: Restart Swift app

## 🔮 **Future Enhancements**

- 📱 Menu bar integration
- 🔊 Voice feedback/confirmation
- 📝 Command templates & shortcuts
- 🌐 Multiple browser support
- 📊 Usage analytics & insights
- 🔄 Session persistence across restarts

## 📄 **License**

This project is provided as-is for demonstration purposes.