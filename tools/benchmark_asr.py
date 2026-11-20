import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import psutil

from local_meeting_interpreter.asr import WhisperRecognizer


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model-root", type=Path, default=project_root / "models")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    process = psutil.Process(os.getpid())
    started = time.perf_counter()
    recognizer = WhisperRecognizer(args.model_root / "faster-whisper-small", cpu_threads=args.threads)
    load_seconds = round(time.perf_counter() - started, 3)
    started = time.perf_counter()
    transcript = recognizer.transcribe(args.audio)
    elapsed_seconds = round(time.perf_counter() - started, 3)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audio": str(args.audio),
        "model_load_seconds": load_seconds,
        "transcription_seconds": elapsed_seconds,
        "real_time_factor": round(elapsed_seconds / transcript.duration, 3),
        "process_rss_mb": round(process.memory_info().rss / 1024 / 1024, 1),
        "language": transcript.language,
        "language_probability": transcript.language_probability,
        "text": transcript.text,
        "segments": [asdict(segment) for segment in transcript.segments],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    report_dir = project_root / "reports"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / f"asr-benchmark-{args.audio.stem}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

