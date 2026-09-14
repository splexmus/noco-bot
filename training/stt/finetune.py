from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import evaluate
import numpy as np
import soundfile as sf
import torch
from datasets import DatasetDict, load_dataset
from scipy.signal import resample_poly
from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    WhisperForConditionalGeneration,
    WhisperProcessor,
    set_seed,
)


SAMPLE_RATE = 16_000


@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        input_features = [
            {"input_features": feature["input_features"]} for feature in features
        ]
        batch = self.processor.feature_extractor.pad(
            input_features,
            return_tensors="pt",
        )

        label_features = [
            {"input_ids": feature["labels"]} for feature in features
        ]
        labels_batch = self.processor.tokenizer.pad(
            label_features,
            return_tensors="pt",
        )
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1),
            -100,
        )
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune Hugging Face Whisper for NOCO speech recognition"
    )
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--eval-manifest", type=Path, required=True)
    parser.add_argument("--model-id", default="openai/whisper-small")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/stt"))
    parser.add_argument("--language", default="th")
    parser.add_argument("--max-steps", type=int, default=2_000)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--warmup-steps", type=int, default=200)
    parser.add_argument("--eval-steps", type=int, default=250)
    parser.add_argument("--save-steps", type=int, default=250)
    parser.add_argument("--logging-steps", type=int, default=25)
    parser.add_argument("--num-proc", type=int, default=1)
    parser.add_argument("--min-duration-seconds", type=float, default=0.2)
    parser.add_argument("--max-duration-seconds", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--freeze-encoder", action="store_true")
    parser.add_argument("--push-to-hub", action="store_true")
    parser.add_argument("--resume-from-checkpoint")
    return parser.parse_args()


def load_audio(path: Path) -> np.ndarray:
    audio, sampling_rate = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if audio.ndim != 1 or audio.size == 0:
        raise ValueError(f"Expected non-empty mono audio: {path}")
    if sampling_rate != SAMPLE_RATE:
        divisor = math.gcd(sampling_rate, SAMPLE_RATE)
        audio = resample_poly(
            audio,
            SAMPLE_RATE // divisor,
            sampling_rate // divisor,
        ).astype(np.float32)
    return np.clip(audio, -1.0, 1.0)


def resolve_audio_path(audio_path: str, manifest_path: Path) -> Path:
    path = Path(audio_path).expanduser()
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def prepare_dataset(
    dataset,
    processor: WhisperProcessor,
    manifest_path: Path,
    num_proc: int,
    min_duration_seconds: float,
    max_duration_seconds: float,
):
    required_columns = {"audio", "text"}
    missing_columns = required_columns.difference(dataset.column_names)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Manifest is missing required columns: {missing}")

    def prepare(example: dict[str, Any]) -> dict[str, Any]:
        audio_path = resolve_audio_path(example["audio"], manifest_path)
        audio = load_audio(audio_path)
        transcript = str(example["text"]).strip()
        if not transcript:
            raise ValueError(f"Transcript must not be empty: {audio_path}")
        input_features = processor.feature_extractor(
            audio,
            sampling_rate=SAMPLE_RATE,
        ).input_features[0]
        labels = processor.tokenizer(transcript).input_ids
        return {
            "input_features": input_features,
            "labels": labels,
            "duration_seconds": len(audio) / SAMPLE_RATE,
        }

    prepared = dataset.map(
        prepare,
        remove_columns=dataset.column_names,
        num_proc=num_proc,
        desc=f"Preparing {manifest_path.name}",
    )
    return prepared.filter(
        lambda example: (
            min_duration_seconds
            <= example["duration_seconds"]
            <= max_duration_seconds
        ),
        num_proc=num_proc,
        desc=f"Filtering {manifest_path.name} by duration",
    )


def main() -> None:
    args = parse_args()
    if args.fp16 and args.bf16:
        raise ValueError("Choose only one of --fp16 or --bf16")
    if args.max_steps <= 0 or args.eval_steps <= 0 or args.save_steps <= 0:
        raise ValueError("Training, evaluation, and save steps must be positive")
    if not 0 < args.min_duration_seconds <= args.max_duration_seconds <= 30:
        raise ValueError("Audio duration limits must satisfy 0 < min <= max <= 30")
    eval_steps = min(args.eval_steps, args.max_steps)
    save_steps = min(args.save_steps, args.max_steps)
    if save_steps % eval_steps != 0:
        raise ValueError("--save-steps must be a multiple of --eval-steps")
    set_seed(args.seed)

    manifests = {
        "train": str(args.train_manifest.resolve()),
        "validation": str(args.eval_manifest.resolve()),
    }
    raw_datasets: DatasetDict = load_dataset("json", data_files=manifests)

    processor = WhisperProcessor.from_pretrained(
        args.model_id,
        language=args.language,
        task="transcribe",
    )
    model = WhisperForConditionalGeneration.from_pretrained(args.model_id)
    model.generation_config.language = args.language
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None
    model.config.use_cache = False
    if args.freeze_encoder:
        model.freeze_encoder()

    prepared = DatasetDict(
        {
            split: prepare_dataset(
                dataset,
                processor,
                args.train_manifest if split == "train" else args.eval_manifest,
                args.num_proc,
                args.min_duration_seconds,
                args.max_duration_seconds,
            )
            for split, dataset in raw_datasets.items()
        }
    )
    if not prepared["train"] or not prepared["validation"]:
        raise ValueError(
            "Training and validation datasets must contain usable audio clips"
        )

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id,
    )
    wer_metric = evaluate.load("wer")

    def compute_metrics(prediction) -> dict[str, float]:
        prediction_ids = prediction.predictions
        if isinstance(prediction_ids, tuple):
            prediction_ids = prediction_ids[0]
        label_ids = prediction.label_ids.copy()
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        predictions = processor.tokenizer.batch_decode(
            prediction_ids,
            skip_special_tokens=True,
        )
        references = processor.tokenizer.batch_decode(
            label_ids,
            skip_special_tokens=True,
        )
        return {
            "wer": 100
            * wer_metric.compute(
                predictions=predictions,
                references=references,
            )
        }

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=min(args.warmup_steps, max(0, args.max_steps // 10)),
        max_steps=args.max_steps,
        gradient_checkpointing=True,
        fp16=args.fp16,
        bf16=args.bf16,
        eval_strategy="steps",
        save_strategy="steps",
        eval_steps=eval_steps,
        save_steps=save_steps,
        logging_steps=args.logging_steps,
        predict_with_generate=True,
        generation_max_length=225,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        report_to="none",
        push_to_hub=args.push_to_hub,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=prepared["train"],
        eval_dataset=prepared["validation"],
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        processing_class=processor,
    )
    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_model()
    processor.save_pretrained(args.output_dir)
    if args.push_to_hub:
        trainer.push_to_hub()


if __name__ == "__main__":
    main()
