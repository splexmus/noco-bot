# Whisper fine-tuning

Prepare separate training and validation JSONL manifests. Each line contains an audio path and its exact transcript:

```json
{"audio":"audio/train/example.wav","text":"สวัสดี โนโค"}
```

Relative audio paths are resolved from the manifest directory. WAV, FLAC, and other formats supported by SoundFile can be used. Audio is converted to mono and resampled to 16 kHz during preprocessing.

By default, clips shorter than 0.2 seconds or longer than 30 seconds are removed. Change the bounds with `--min-duration-seconds` and `--max-duration-seconds`, keeping the maximum at or below Whisper's 30-second training window.

Create the training environment and run a small smoke training job first:

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

For a full CUDA run, select the precision supported by the GPU and increase the step count:

```bash
python -m training.stt.finetune \
  --train-manifest data/train.jsonl \
  --eval-manifest data/validation.jsonl \
  --output-dir artifacts/whisper-noco \
  --model-id openai/whisper-small \
  --language th \
  --max-steps 2000 \
  --fp16
```

Use `--resume-from-checkpoint artifacts/whisper-noco/checkpoint-N` to resume. Add `--push-to-hub` only after authenticating with `huggingface-cli login`.

After training, point inference at the local artifact:

```bash
STT_MODEL_ID=artifacts/whisper-noco uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Keep speakers disjoint between training and validation, normalize transcript conventions before training, and inspect WER together with real robot recordings. Do not commit private recordings, generated checkpoints, or Hugging Face credentials.
