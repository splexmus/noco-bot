# NOCO Bot

NOCO is a local voice-assistant prototype with a robot client and a central AI server. The robot listens for `hey_noco`, records speech, sends it to the server for transcription and chat, receives synthesized speech, and plays the response. An animated fullscreen face communicates the robot's current state.

The robot also exposes a small FastAPI image service. This lets the central server send a JPEG to the robot even though the robot is normally the client of the voice API.

## Architecture

```text
Robot / edge device                         Central compute server
-------------------                         ----------------------
Microphone -> Wake word -> VAD/Recorder
                    POST /stt ------------> Whisper
                    POST /chat -----------> Ollama + Chroma
Speaker <----------- POST /tts ------------ Piper
    |
Face display: waiting / listening / thinking / speaking / error

POST /image receiver <--------------------- image sender
```

The applications are separate processes:

- `server.app:app` is the central API on port `8000`.
- `client.app` is the reusable robot voice loop and state source.
- `client.display` is the robot face application; it runs the voice loop in a worker thread.
- `client.api:app` is the robot image receiver on port `8001`.

When the robot and server are different machines, set `SERVER_HOST` in `client/config.py` to the server's LAN address. The central image sender must likewise address the robot's LAN IP, not `localhost`.

## Main components

```text
client/
  app.py                    Robot voice state machine
  audio/                    Microphone, VAD, recorder, and playback
  wakeword/                 OpenWakeWord integration and local models
  networks/                 STT, chat, and TTS HTTP clients
  display/                  Animated Tkinter face and screen application
  api/                      Robot-side image receiver
    image/
      image_engine.py       JPEG validation and atomic storage
      image_service.py      GET and POST /image routes
      img.jpg               Current robot image (provided at runtime)
server/
  app.py                    Central FastAPI application
  stt/                      Faster Whisper transcription
  chat/ and llm/            Chat route and Ollama integration
  memory/                   Chroma vector memory
  tts/                      Piper speech synthesis
environments/               Conda environment exports
```

## Setup

The checked-in Conda files are exports from the development machines and contain machine-specific `prefix:` fields. Remove those fields or let Conda choose a local path when installing elsewhere.

Create the robot and server environments:

```bash
conda env create -f environments/robot.yml
conda env create -f environments/stt.yml
```

The central server requires its local models and an Ollama service. The default chat model is `gemma4:e4b`, and memory embeddings use `nomic-embed-text` at `http://localhost:11434`.

## Run the central voice API

Run commands from the repository root because some model and database paths are relative to it:

```bash
conda activate stt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Available routes:

- `GET /health`
- `POST /stt`
- `POST /chat`
- `POST /tts`

## Run the robot

Start the image receiver in one terminal:

```bash
conda activate robot
uvicorn client.api:app --host 0.0.0.0 --port 8001
```

Start the face display and voice loop together in another terminal:

```bash
conda activate robot
python -m client.display
```

The display opens fullscreen. Press `F11` to toggle fullscreen, or `Escape` to leave it. Press `q` to close the application cleanly.

To preview every expression without loading models, connecting to the server, or using audio hardware:

```bash
python -m client.display --demo --windowed
```

For a headless robot, run only the voice loop:

```bash
conda activate robot
python -m client.app
```

The voice loop requires a working microphone and speaker. It uses 16 kHz mono audio with 512-sample frames.

## Customize the robot face

The face uses Tkinter Canvas shapes, so it does not require image assets or an additional GUI dependency. Customize it in `client/display/face.py`:

- Change colors, font, eye spacing, sizing, and line width in `FaceTheme`.
- Change per-state eye openness, pupil movement, and mouth type in `EXPRESSIONS`.
- Edit `_draw_eyes`, `_draw_mouth`, or `_draw_ambient` to create new shapes and animations.
- Add a state to `FaceState`, then add its geometry to `EXPRESSIONS` and its pipeline mapping to `STATE_ALIASES`.

The voice state mapping is:

| Voice state | Face expression |
| --- | --- |
| `WAITING` | Waiting with periodic blink |
| `LISTENING` | Wide eyes and a pulsing listening ring |
| `STT_REQUEST` | Thinking |
| `CHAT_REQUEST` | Thinking |
| `TTS_REQUEST` | Animated speaking mouth |
| `ERROR` | Red error expression |

## Image API

The image receiver stores the current image at `client/api/image/img.jpg`. The file may already exist at startup; otherwise the first valid upload creates it.

### Send or replace the image

```bash
curl --fail-with-body \
  -X POST \
  -H 'Content-Type: image/jpeg' \
  --data-binary '@/path/to/image.jpg' \
  http://ROBOT_IP:8001/image
```

A successful upload returns HTTP `201` and metadata similar to:

```json
{
  "status": "stored",
  "filename": "img.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 12345,
  "sha256": "..."
}
```

The receiver accepts JPEG data only, rejects empty or malformed bodies, and limits uploads to 10 MiB. It writes through a temporary file so readers never see a partially uploaded image.

### Read the current image

```bash
curl --fail http://ROBOT_IP:8001/image --output received.jpg
```

`GET /image` returns `404` until `img.jpg` exists. Check receiver availability with:

```bash
curl --fail http://ROBOT_IP:8001/health
```

## API payloads

- `/stt` accepts an `.npy` byte stream created with `numpy.save` and returns transcription JSON.
- `/chat` accepts `{ "text": "..." }` and returns `{ "response": "..." }`.
- `/tts` accepts `{ "text": "..." }` and returns synthesized audio bytes.
- The robot-side `/image` accepts raw JPEG bytes with `Content-Type: image/jpeg`.

## Testing

Compile the Python packages after changes:

```bash
python -m compileall client server
python -m unittest client.tests.test_display -v
```

Files under `client/tests/` and `server/tests/` are primarily manual integration scripts. Many require audio hardware, downloaded models, or a live Ollama process; they are not yet an isolated unit-test suite.

## Current limitations

- `server/requirements.txt` and `docker/requirements.txt` are empty; use the Conda environments for now.
- Importing the central app initializes heavyweight model services immediately.
- The existing TTS server serializes with `numpy.save`, while the client currently reads raw `int16`; this wire-format mismatch still needs correction.
- Conversation persistence is disabled in the chat route because `memory.add(...)` is commented out.

See `AGENTS.md` for code conventions, known review findings, and the intended network boundaries.
