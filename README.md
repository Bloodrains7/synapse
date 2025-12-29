# Synapse - Voice Commander for Test Automation

Voice-controlled orchestration layer for the test automation microservices ecosystem (Scout, Golem, Marker).

## Overview

Synapse uses Google Gemini LLM to process voice commands and coordinate test automation tasks across multiple microservices:

- **Scout** - Generate test scenarios from frontend code
- **Golem** - Generate and run Playwright/Robot/Cypress tests
- **Marker** - Add data-testid attributes to frontend elements

## Features

- Voice command recognition (Slovak/English)
- Natural language intent parsing with Gemini
- Test scenario dictation
- gRPC communication with microservices
- Text mode for testing without microphone

## Requirements

- Python 3.10+ (tested with 3.14)
- Google Gemini API key
- Running Scout, Golem, Marker gRPC services
- PyAudio (optional, only for voice mode)

## Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# For voice mode (optional):
# Windows: pip install pipwin && pipwin install pyaudio
# macOS: brew install portaudio && pip install pyaudio
# Linux: sudo apt-get install portaudio19-dev && pip install pyaudio

# Configure environment
cp .env.example .env
# Edit .env with your Gemini API key
```

## Usage

### Text Mode (recommended for testing)
```bash
python main.py text
```

### Voice Mode (requires PyAudio)
```bash
python main.py voice
python main.py voice --language en-US
```

### Single Command
```bash
python main.py command "Generate test scenarios for C:/path/to/project"
```

## Commands (Voice or Text)

- "Vygeneruj testovacie scenare pre C:/path/to/project" - Generate test scenarios
- "Vygeneruj Playwright testy zo scenarios.json" - Generate tests from scenarios
- "Spusti testy v result/tests proti localhost:4200" - Run tests
- "Pridaj test ID atributy do C:/path/to/project" - Add test IDs
- "Nadiktujem scenar: klikni na button a over message" - Dictate a scenario
- "stop" / "koniec" / "exit" - Exit

## Architecture

```
Synapse (Voice Commander)
    |
    +-- VoiceInput (Speech Recognition)
    +-- CommandParser (Gemini LLM)
    +-- gRPC Clients
            |
            +-- Scout  :50051
            +-- Golem  :50052
            +-- Marker :50053
```
