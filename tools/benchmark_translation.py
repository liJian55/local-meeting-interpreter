import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from local_meeting_interpreter.translation import OpusTranslator


SAMPLES = {
    "zh-en": [
        "你好，很高兴参加今天的会议。",
        "我们明天上午十点讨论下一版本的发布计划。",
        "请确认订单中的乘客姓名、航班号和到达时间是否正确。",
        "这个方案可以先在本机验证，识别和翻译的延迟都能接受之后再接入实时会议音频。",
    ],
    "en-zh": [
        "Hello, it is a pleasure to join today's meeting.",
        "We will discuss the next release plan at ten tomorrow morning.",
        "Please confirm that the passenger name, flight number, and arrival time are correct.",
        "We can validate this approach on the local machine first, then connect it to the live meeting audio.",
    ],
}


def memory_mb(process: psutil.Process) -> float:
    return round(process.memory_info().rss / 1024 / 1024, 1)


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", choices=(*SAMPLES, "both"), default="both")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--model-root", type=Path, default=project_root / "models")
    args = parser.parse_args()
    process = psutil.Process(os.getpid())
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runs_per_sample": args.runs,
        "threads": args.threads,
        "device": "cpu",
        "directions": {},
    }
    directions = SAMPLES if args.direction == "both" else (args.direction,)
    for direction in directions:
        model_dir = args.model_root / f"opus-mt-{direction}-ct2-int8"
        started = time.perf_counter()
        translator = OpusTranslator(model_dir, intra_threads=args.threads)
        load_ms = round((time.perf_counter() - started) * 1000, 1)
        results = []
        for sample in SAMPLES[direction]:
            timings = []
            translated = ""
            for _ in range(args.runs):
                started = time.perf_counter()
                translated = translator.translate(sample)
                timings.append(round((time.perf_counter() - started) * 1000, 1))
            results.append({
                "source": sample,
                "translation": translated,
                "warm_ms": timings[1:],
                "median_warm_ms": round(statistics.median(timings[1:] or timings), 1),
            })
        report["directions"][direction] = {
            "load_ms": load_ms,
            "model_disk_mb": round(sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file()) / 1024 / 1024, 1),
            "process_rss_mb": memory_mb(process),
            "samples": results,
        }
        print(f"{direction}: load {load_ms} ms, RSS {memory_mb(process)} MB", flush=True)
        for result in results:
            print(f"  {result['source']}\n  {result['translation']}\n  median {result['median_warm_ms']} ms", flush=True)
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"translation-benchmark-{args.direction}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()

