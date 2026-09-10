# NOCO Bot Agent Guide

## Project purpose

NOCO Bot is a local, client/server voice assistant. The robot-side process captures microphone audio, detects the `hey_noco` wake word, records speech, and calls a central FastAPI service for speech-to-text (STT), chat, and text-to-speech (TTS). The response audio is then played on the robot.

The planned image path is bidirectional in terms of machine roles: the robot is a **client** of the central voice API, but the same robot must also run an **image receiver server** so the central server can send an image back to it.

## Runtime topology

Keep these two HTTP applications and their traffic directions distinct:

```text
Robot / edge device                         Central compute server
-------------------                         ----------------------
client.app (voice state machine)
    POST audio/text ----------------------> server.app
                                             /stt
                                             /chat
    <------------------------- audio         /tts

robot image receiver <-------------------- central image sender
    POST /image
```

- `server.app:app` is the central FastAPI app. It owns `/stt`, `/chat`, `/tts`, `/health`, and `/`.
- `client.app` is the long-running robot voice state machine and an HTTP client of `server.app`.
- The robot-side image API is intended to accept inbound `POST /image` calls from the central server. It is a separate process from `client.app` even when both run on the same robot.
- Bind the robot image receiver to `0.0.0.0` when another machine must reach it. Configure the sender with the robot's LAN address; `localhost` only works when sender and receiver are on the same machine.
- Use a different port for the robot image receiver (for example `8001`) and the central API (`8000`). Do not overload `client.config.BASE_URL`: that value identifies the central server from the robot's point of view.

## Current implementation status

The voice path exists, though it remains prototype-quality. The robot-side image receiver is implemented in the `client.api` package:

- Run it with `uvicorn client.api:app --host 0.0.0.0 --port 8001`.
- `POST /image` validates JPEG bytes and atomically stores them as `client/api/image/img.jpg`.
- `GET /image` returns the current JPEG, and `GET /health` checks receiver availability.
- Uploads are limited to 10 MiB. Empty, unsupported, and malformed payloads are rejected.
- The legacy `client/api.py` file is only a compatibility entry point; Python normally imports the `client/api/` package for `client.api`.
- No automatic central-server image sender, authentication, or image display integration exists yet.

## Intended image contract

Unless a task specifies a different protocol, implement the smallest interoperable contract:

- Direction: central server sends; robot-side image server receives.
- Method and path: `POST /image` on the robot image receiver.
- Body: encoded image bytes, not a NumPy serialization.
- Request `Content-Type`: `image/jpeg`.
- Success response: JSON containing at least `status`, `content_type`, and `size_bytes`; use an appropriate 2xx status.
- Reject empty bodies, unsupported media types, malformed images, and oversized requests with clear 4xx responses.
- Decode images in memory first. Do not trust a sender-provided filename or write outside a configured image directory.
- Put outbound HTTP behavior in a dedicated network class, consistent with `client/networks/api_client.py`; do not mix transport logic into an image engine.
- Keep receiving separate from presentation. The route validates input, an engine/storage component owns decode/save/display behavior, and the caller receives a typed response.
- Add a health endpoint to the robot image server so the central sender can distinguish an unavailable robot from an invalid image.

If the required behavior is instead robot-to-central image upload, confirm that direction before implementation; it is the reverse of the topology documented here.

## Code map

- `client/app.py`: synchronous voice-assistant state machine: waiting, listening, STT, chat, TTS.
- `client/audio/`: microphone capture, Silero VAD, recording, and playback.
- `client/wakeword/`: OpenWakeWord wrapper using models in `client/models/`.
- `client/networks/`: blocking `requests` clients for the central API.
- `client/config.py`: central API host, port, and base URL. It currently defaults to `localhost:8000`.
- `client/api/`: robot-side image receiver and JPEG storage engine.
- `server/app.py`: central FastAPI composition root.
- `server/stt/`: Faster Whisper engine and `/stt` route.
- `server/chat/`, `server/llm/`, `server/memory/`: Ollama chat plus Chroma/Ollama-backed memory lookup.
- `server/tts/`: Piper synthesis and `/tts` route.
- `environments/`: exported Conda environments. `robot.yml` is robot-side; the other files cover service dependencies.
- `client/tests/` and `server/tests/`: mostly manual executable checks, not an isolated automated test suite.

## Existing wire formats

- `POST /stt`: body is an `.npy` payload created with `numpy.save`; response is JSON with `text`, language metadata, and timestamped segments.
- `POST /chat`: JSON `{ "text": "..." }`; response is JSON `{ "response": "..." }`.
- `POST /tts`: JSON `{ "text": "..." }`; intended response is synthesized PCM audio.

Do not silently change an existing endpoint's wire format. Update both producer and consumer together and add a round-trip test.

## Development and verification

Run commands from the repository root because several model and database paths are relative to it.

```bash
conda env create -f environments/robot.yml
conda env create -f environments/stt.yml
conda activate stt
uvicorn server.app:app --host 0.0.0.0 --port 8000
conda activate robot
python -m client.app
```

The environment exports include machine-specific `prefix:` values. Remove or override those when recreating environments on another host. `server/requirements.txt` and `docker/requirements.txt` are currently empty, and the Dockerfile is not a reliable setup path.

Before handing off changes:

1. Compile changed Python modules with `python -m compileall client server`.
2. Exercise `/health` for every FastAPI process that was changed.
3. Test HTTP contracts through both sender and receiver; do not test only route internals.
4. For image work, cover a valid JPEG or PNG, an empty body, an unsupported content type, malformed bytes, and the configured size limit.
5. State which checks require unavailable hardware, local models, Ollama, or audio devices.

## Known review findings

Account for these when working near the affected code:

- `client/networks/tts_client.py` reads the response as raw `int16`, but `server/tts/tts_service.py` wraps audio with `numpy.save`. The `.npy` header will be interpreted as samples. Fix both sides together or load the response with `numpy.load`.
- In `client/app.py`, the empty-STT-result branch references `e` when no exception is active.
- Service engines are constructed at module import time. Starting `server.app` immediately loads Whisper, Piper, Chroma, and Ollama-related resources; tests and lightweight health checks are therefore expensive and environment-dependent.
- `server/memory/chroma_store.py` uses a working-directory-relative database path and assumes a local Ollama embedding service at port `11434`.
- `server/llm/__inti__.py` is misspelled.
- Most files under `client/tests/` and `server/tests/` are interactive scripts with hardware/model dependencies and few or no assertions. Do not assume `pytest` provides a clean unit-test signal.
- Memory persistence in `server/chat/chat_service.py` is disabled because `memory.add(...)` is commented out.
- Avoid committing generated audio, logs, Chroma data, caches, machine-specific paths, or model binaries unless the task explicitly calls for them.

## Change conventions

- Preserve the boundary between hardware-facing client code and compute-heavy server code.
- Keep sample rate, frame size, audio dtype, content type, and response schema explicit at network boundaries.
- Prefer typed Pydantic request/response models for JSON APIs and explicit FastAPI `Response` objects for binary APIs.
- Use timeouts for outbound calls and turn connection/validation failures into actionable errors.
- Avoid heavy initialization during imports in new code; use FastAPI lifespan management or dependency injection where practical.
- Use `pathlib.Path` anchored to the module/repository location instead of relying on the current working directory for new file paths.
- Add focused automated tests for new logic. Keep hardware, model-download, and live-Ollama checks clearly marked as integration/manual tests.
- Never deserialize untrusted image requests with pickle-enabled NumPy loading. Validate byte length and image structure before use.
