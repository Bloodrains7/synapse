# Synapse - Voice Commander Architecture

## Overview
AI-powered voice command system for generating test scenarios and Playwright tests using CrewAI and Gemini LLM.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYNAPSE                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Voice Input  │───>│   Command    │───>│   CrewAI     │       │
│  │   (STT)      │    │   Parser     │    │ Orchestrator │       │
│  └──────────────┘    └──────────────┘    └──────┬───────┘       │
│                                                  │               │
│                    ┌─────────────────────────────┼───────┐       │
│                    │                             │       │       │
│              ┌─────▼─────┐  ┌─────────────┐  ┌───▼─────┐ │       │
│              │ Scenario  │  │  Playwright │  │  Code   │ │       │
│              │ Generator │  │  Generator  │  │ Review  │ │       │
│              │   Agent   │  │    Agent    │  │  Agent  │ │       │
│              └─────┬─────┘  └──────┬──────┘  └────┬────┘ │       │
│                    │               │              │       │       │
│                    └───────────────┼──────────────┘       │       │
│                                    │                      │       │
│                             ┌──────▼──────┐               │       │
│                             │   Gemini    │               │       │
│                             │     LLM     │               │       │
│                             └──────┬──────┘               │       │
│                                    │                      │       │
│                             ┌──────▼──────┐               │       │
│                             │   Output    │               │       │
│                             │  Generator  │               │       │
│                             └─────────────┘               │       │
│                                                           │       │
└───────────────────────────────────────────────────────────┴───────┘
```

## Components

### 1. Voice Input Module
- **Technology**: Google Speech Recognition / Whisper
- **Purpose**: Convert voice commands to text
- **Features**:
  - Real-time transcription
  - Multi-language support
  - Noise cancellation

### 2. Command Parser
- **Purpose**: Parse and classify voice commands
- **Command Types**:
  - `generate scenarios for [feature]` - Generate test scenarios
  - `create playwright tests for [component]` - Generate Playwright tests
  - `dictate scenario` - Record a test scenario via voice
  - `review code [file]` - Code review

### 3. CrewAI Orchestrator
- **Purpose**: Coordinate AI agents
- **Agents**:
  - **Scenario Generator Agent**: Creates test scenarios based on requirements
  - **Playwright Generator Agent**: Converts scenarios to Playwright code
  - **Code Review Agent**: Reviews generated code for best practices

### 4. Gemini LLM Integration
- **Model**: gemini-2.0-flash or gemini-pro
- **Purpose**: Power all AI agents
- **Features**:
  - Long context understanding
  - Code generation
  - Multi-modal support (future: screenshots)

### 5. Output Generator
- **Formats**:
  - Gherkin/BDD scenarios (.feature)
  - Playwright TypeScript tests (.spec.ts)
  - Test documentation (.md)

## Data Flow

1. User speaks command
2. STT converts to text
3. Parser classifies intent
4. CrewAI dispatches to appropriate agent(s)
5. Agent(s) process with Gemini LLM
6. Output generated and saved

## File Structure

```
synapse/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── recorder.py      # Audio recording
│   │   └── transcriber.py   # STT processing
│   ├── parser/
│   │   ├── __init__.py
│   │   └── command_parser.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── crew.py          # CrewAI setup
│   │   ├── scenario_agent.py
│   │   ├── playwright_agent.py
│   │   └── review_agent.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── scenario_generator.py
│   │   └── playwright_generator.py
│   └── output/
│       ├── __init__.py
│       └── writer.py
├── templates/
│   ├── scenario.feature.j2
│   └── playwright.spec.ts.j2
├── output/                   # Generated files
├── .env
├── requirements.txt
└── README.md
```

## Command Examples

```bash
# Generate test scenarios
"Generate test scenarios for user login with email and password"

# Generate Playwright tests
"Create Playwright tests for the shopping cart checkout flow"

# Dictate scenario
"Dictate scenario: User opens homepage, clicks login button, enters email..."

# Generate from existing scenarios
"Generate Playwright tests from scenarios in features/login.feature"
```
