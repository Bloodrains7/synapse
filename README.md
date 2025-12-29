# Synapse - Voice Commander for Test Automation

Real-time voice-controlled orchestration layer for the test automation microservices ecosystem using **Gemini Live API**.

## Overview

Synapse uses Google Gemini Live API for real-time bidirectional voice communication. You speak, the AI listens and responds with voice, then executes test automation tasks:

- **Scout** - Generate test scenarios from frontend code
- **Golem** - Generate and run Playwright/Robot/Cypress tests
- **Marker** - Add data-testid attributes to frontend elements

## Features

- **Real-time voice conversation** with Gemini Live API
- Bidirectional audio - speak and hear responses
- Natural language understanding (Slovak/English)
- Tool execution for test automation tasks
- gRPC communication with microservices
- Text mode for testing without microphone

## Requirements

- Python 3.10+ (tested with 3.14)
- Google API key with Gemini Live API access
- Running Scout, Golem, Marker gRPC services (for test automation)

## Installation

```bash
# Install all dependencies (no compilation needed!)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
```

All dependencies have prebuilt wheels for Windows/macOS/Linux - no Visual C++ Build Tools needed.

## Usage

### Live Voice Mode (Gemini Live API)
```bash
python main.py live
```
- Uses real-time bidirectional audio
- Model speaks responses back to you
- **Use headphones** to prevent echo!

### Text Mode
```bash
python main.py text
```

### Single Command
```bash
python main.py command "Generate scenarios for C:/Projects/my-app"
```

### List Audio Devices
```bash
python main.py devices
```

## Voice Commands

Speak naturally in Slovak or English:

- "Vygeneruj testovacie scenare pre C:/Projects/company-angular"
- "Generate Playwright tests from result/scenarios.json"
- "Run tests in result/tests against localhost:4200"
- "Add test IDs to the company-angular project"
- "Stop" / "Koniec" / "Exit" - End session

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         SYNAPSE                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Live Voice  │◄─┼─► Gemini    │──► Tool Handler        │  │
│  │ (PyAudio)   │  │  Live API   │  │ (gRPC Clients)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Microservices  │
                    │  Scout :50051   │
                    │  Golem :50052   │
                    │  Marker :50053  │
                    └─────────────────┘
```

## Project Structure

```
synapse/
├── main.py           # CLI entry point
├── config.py         # Configuration
├── live_voice.py     # Gemini Live API integration
├── agents.py         # Tool handlers
├── grpc_clients.py   # Scout/Golem/Marker clients
├── requirements.txt  # Dependencies
├── .env.example      # Environment template
└── README.md         # This file
```

## Configuration

`.env` file:
```env
GOOGLE_API_KEY=your-api-key-here
GEMINI_LIVE_MODEL=gemini-2.0-flash-live-001
GEMINI_TEXT_MODEL=gemini-2.0-flash

SCOUT_GRPC_HOST=localhost:50051
GOLEM_GRPC_HOST=localhost:50052
MARKER_GRPC_HOST=localhost:50053
```

## License

MIT
