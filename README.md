# NOCO Bot

A voice-controlled AI assistant that combines wake-word detection, speech-to-text, conversational AI, and text-to-speech capabilities into a single integrated system.

## Overview

NOCO is an intelligent voice assistant that operates entirely on-device with a modular architecture. It listens for a wake word ("hey_noco"), captures audio when activated, transcribes speech to text, processes the query through an LLM, generates responses, and converts them back to speech for playback.

## Features

- **Wake-word Detection**: Listens for "hey_noco" to activate the assistant
- **Voice Activity Detection (VAD)**: Detects when user is speaking
- **Speech-to-Text (STT)**: Converts spoken words to text using Whisper
- **Conversational AI**: Processes user queries through an LLM
- **Text-to-Speech (TTS)**: Converts text responses back to audio
- **On-device Processing**: All processing happens locally without cloud dependencies

## Architecture

```
[Microphone] → [Wake-word Detector] → [VAD] → [STT] → [LLM Chat] → [TTS] → [Speaker]
     ↑              ↓               ↓         ↑           ↓          ↓        ↑
  Audio    Wake-word      Audio   Transcribed   Response   Synthesized  Audio
           Detection    Detection    Text         Text       Speech     Playback
```

## Components

### Client Side (Local Processing)
- `client/app.py`: Main application logic with state machine
- `client/audio/`: Audio handling components
  - `microphone.py`: Audio input management
  - `player.py`: Audio output management  
  - `recorder.py`: Audio recording with VAD
- `client/networks/`: Network communication for services
  - `ChatClient`: Communicates with chat service
  - `STTClient`: Communicates with STT service  
  - `TTSClient`: Communicates with TTS service
- `client/wakeword/`: Wake word detection implementation

### Server Side (API Services)
- `server/app.py`: FastAPI application with routers
- `server/stt/`: Speech-to-text service using Whisper
- `server/chat/`: Chat and LLM processing service  
- `server/tts/`: Text-to-speech service

## Setup and Installation

1. **Prerequisites**:
   - Python 3.8+
   - Required packages in `requirements.txt`

2. **Installation**:
   ```bash
   # Install dependencies
   pip install -r server/requirements.txt
   ```

3. **Usage**:
   ```bash
   # Run the client application
   python -m client.app
   
   # Or for testing wake word detection
   python -m client.tests.wakeword_test
   ```

## Project Structure

```
noco_bot/
├── client/                 # Client-side components
│   ├── app.py             # Main application logic
│   ├── audio/             # Audio processing modules
│   ├── networks/          # Network clients for server services
│   └── tests/             # Test files
├── server/                # Server-side API services  
│   ├── app.py             # FastAPI application
│   ├── stt/               # STT service implementation
│   ├── chat/              # Chat/LLM service implementation
│   ├── tts/               # TTS service implementation
│   └── requirements.txt   # Server dependencies
├── docker/                # Docker configuration files
├── environments/          # Environment configurations
└── README.md              # This file
```

## Development

This project is designed for educational purposes to demonstrate:
- Voice assistant architecture
- Audio signal processing (VAD, wake-word detection)
- Natural language processing pipeline
- Client-server communication patterns
- Modular system design principles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational purposes.