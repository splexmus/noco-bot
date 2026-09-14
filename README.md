# NOCO Bot

NOCO is a local voice-assistant prototype with a robot client and a central AI server. The robot listens for `hey_noco`, records speech, sends it to the server for transcription and chat, receives synthesized speech, and plays the response. An animated fullscreen face communicates the robot's current state.

The robot also exposes a small FastAPI image service. The server can request a fresh camera JPEG for Ollama vision analysis, and another service can replace the stored JPEG through the upload route.

## Architecture

```text
Robot / edge device                         Central compute server
-------------------                         ----------------------
Microphone -> Wake word -> VAD/Recorder
                    POST /stt ------------> Hugging Face Whisper
                    POST /chat -----------> Ollama + Chroma
Speaker <----------- POST /tts ------------ Piper
    |
Face display: waiting / listening / thinking / speaking / error

POST /camera/capture -------------------> camera tool -> vision model
POST /image receiver <-------------------- image producer
```

The applications are separate processes:

- `server.app:app` is the central API on port `8000`.
- `client.app` is the reusable robot voice loop and state source.
- `client.display` is the robot face application; it runs the voice loop in a worker thread.
- `client.api:app` is the robot image receiver on port `8001`.

When the robot and server are different machines, set `SERVER_HOST` in `client/config.py` to the server's LAN address. Set `ROBOT_API_URL` on the central server to the robot's LAN address; `localhost` only works when both processes are on the same machine.

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
      image_service.py      Image upload/read and camera capture routes
      camera_engine.py      ffmpeg/V4L2 single-frame capture
      img.jpg               Current robot image (provided at runtime)
server/
  app.py                    Central FastAPI application
  stt/                      Hugging Face Transformers Whisper inference
  chat/ and llm/            Chat route and Ollama integration
  memory/                   Chroma vector memory
  tools/                    Robot camera client used by Ollama
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

The central server requires a local Ollama service and three model capabilities. Defaults are `qwen3:0.6b` for chat/tool selection, `gemma3:4b` for image understanding, and `nomic-embed-text` for memory embeddings.

```bash
ollama pull qwen3:0.6b
ollama pull gemma3:4b
ollama pull nomic-embed-text
```

Override runtime settings with environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `qwen3:0.6b` | Chat and tool-calling model |
| `OLLAMA_VISION_MODEL` | `gemma3:4b` | Camera-image analysis model |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Chroma embedding model |
| `ROBOT_API_URL` | `http://localhost:8001` | Robot image API URL |
| `MEMORY_DB_PATH` | `server/memory/memory_db` | Persistent Chroma directory |
| `STT_MODEL_ID` | `openai/whisper-small` | Hugging Face model or local checkpoint |
| `STT_LANGUAGE` | `th` | Forced Whisper transcription language |
| `STT_DEVICE` | `auto` | `auto`, `cpu`, `cuda`, or `cuda:N` |
| `STT_CHUNK_LENGTH_SECONDS` | `30` | Inference pipeline chunk length |

Robot camera capture requires `ffmpeg` and a V4L2 camera device. Defaults are `/dev/video0` at 640x480. Configure it with `CAMERA_DEVICE`, `CAMERA_WIDTH`, `CAMERA_HEIGHT`, and `CAMERA_CAPTURE_TIMEOUT_SECONDS` on the robot.

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

The Hugging Face Whisper model is loaded lazily on the first `/stt` request. Its first use may download the configured checkpoint from the Hub. With a forced `STT_LANGUAGE`, `language_probability` is `1.0` to indicate configuration rather than measured detection confidence; automatic mode reports `unknown` and `0.0`.

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

## Ollama camera tool

The `/chat` pipeline exposes `capture_camera_image` to the chat model. For a request such as “What do you see?”, the server:

1. Lets the chat model decide whether current visual information is required.
2. Calls `POST http://ROBOT_IP:8001/camera/capture` with a timeout.
3. The robot uses `ffmpeg` to capture one V4L2 frame, stores it as `img.jpg`, and returns it.
4. The server validates the streamed JPEG response and its 10 MiB limit.
5. The server sends the image bytes and the model's question to the vision model.
6. It returns the visual observation as a tool result to the chat model.
7. The chat model produces the final conversational response.

Camera, network, and model errors are returned to the chat model so it can explain that vision is unavailable instead of inventing a visual result. `GET /image` remains available for reading the most recently captured or uploaded frame.

## Conversation memory

Successful `/chat` responses are kept in a bounded in-process history and persisted to Chroma. Relevant prior conversations are retrieved before generation and are clearly marked as contextual data rather than instructions. If embedding search or persistence is temporarily unavailable, chat continues without vector memory.

## Fine-tune Whisper

The training workflow in `training/stt/` consumes train and validation JSONL manifests containing `audio` and `text`. It converts audio to mono 16 kHz, fine-tunes `WhisperForConditionalGeneration`, evaluates word error rate (WER), and saves both the model and processor.

```bash
conda env create -f environments/stt-finetune.yml
conda activate noco-stt-finetune
python -m training.stt.finetune \
  --train-manifest data/train.jsonl \
  --eval-manifest data/validation.jsonl \
  --output-dir artifacts/whisper-noco \
  --language th \
  --max-steps 10
```

Start with this short smoke run before a full GPU job. See `training/stt/README.md` for the manifest format, precision options, checkpoint resume, and deployment instructions.

## API payloads

- `/stt` accepts an `.npy` byte stream created with `numpy.save` and returns transcription JSON.
- `/chat` accepts `{ "text": "..." }` and returns `{ "response": "..." }`.
- `/tts` accepts `{ "text": "..." }` and returns synthesized audio bytes.
- The robot-side `/image` accepts raw JPEG bytes with `Content-Type: image/jpeg`.
- The robot-side `/camera/capture` captures, stores, and returns a fresh JPEG.

## Testing

Compile the Python packages after changes:

```bash
python -m compileall client server
python -m unittest client.tests.test_display -v
python -m unittest client.tests.test_camera_capture -v
conda run -n stt python -m unittest \
  server.tests.test_hf_whisper \
  server.tests.test_stt_service -v
conda run -n stt python -m unittest \
  server.tests.test_memory_engine \
  server.tests.test_chroma_store \
  server.tests.test_camera_tool \
  server.tests.test_ollama_tools \
  server.tests.test_chat_service -v
```

Files under `client/tests/` and `server/tests/` are primarily manual integration scripts. Many require audio hardware, downloaded models, or a live Ollama process; they are not yet an isolated unit-test suite.

## Current limitations

- `server/requirements.txt` and `docker/requirements.txt` are empty; use the Conda environments for now.
- TTS still initializes its model at import time; Hugging Face STT, chat, and memory now initialize lazily.
- The existing TTS server serializes with `numpy.save`, while the client currently reads raw `int16`; this wire-format mismatch still needs correction.
- Camera capture currently supports V4L2 devices through `ffmpeg`; Raspberry Pi CSI cameras may require a different adapter or V4L2 compatibility mode.

See `AGENTS.md` for code conventions, known review findings, and the intended network boundaries.
