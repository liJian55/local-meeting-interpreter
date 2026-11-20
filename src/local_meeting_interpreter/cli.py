import argparse
import json
import sys
from pathlib import Path

from local_meeting_interpreter.asr import WhisperRecognizer
from local_meeting_interpreter.paths import project_root
from local_meeting_interpreter.pipeline import OfflineInterpreter
from local_meeting_interpreter.translation import OpusTranslator


DIRECTIONS = ("zh-en", "en-zh")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding and stream.encoding.lower() != "utf-8":
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Private, offline meeting interpreter.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    translate_parser = subparsers.add_parser("translate", help="Translate text locally.")
    translate_parser.add_argument("text", help="Text to translate.")
    translate_parser.add_argument("direction", choices=DIRECTIONS)
    for command_parser in (translate_parser,):
        command_parser.add_argument("--model-root", type=Path, default=project_root() / "models")
        command_parser.add_argument("--beam-size", type=int, default=1, choices=(1, 2, 4))
        command_parser.add_argument("--threads", type=int, default=4)
        command_parser.add_argument("--json", action="store_true", dest="json_output")
    for command_name in ("transcribe", "interpret"):
        command_parser = subparsers.add_parser(command_name)
        command_parser.add_argument("audio", type=Path)
        command_parser.add_argument("--model-root", type=Path, default=project_root() / "models")
        command_parser.add_argument("--threads", type=int, default=4)
        command_parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    if args.command in ("transcribe", "interpret"):
        recognizer = WhisperRecognizer(args.model_root / "faster-whisper-small", cpu_threads=args.threads)
        if args.command == "transcribe":
            transcript = recognizer.transcribe(args.audio)
            if args.json_output:
                print(json.dumps({
                    "language": transcript.language,
                    "language_probability": transcript.language_probability,
                    "duration": transcript.duration,
                    "text": transcript.text,
                    "segments": [segment.__dict__ for segment in transcript.segments],
                }, ensure_ascii=False))
            else:
                print(transcript.text)
        else:
            interpreter = OfflineInterpreter(recognizer, args.model_root)
            transcript, segments = interpreter.transcribe_and_translate(args.audio)
            if args.json_output:
                print(json.dumps({
                    "language": transcript.language,
                    "duration": transcript.duration,
                    "segments": segments,
                }, ensure_ascii=False))
            else:
                for segment in segments:
                    print(f"[{segment['start']:.2f} -> {segment['end']:.2f}] {segment['text']}")
                    print(segment["translation"])
        return

    model_dir = args.model_root / f"opus-mt-{args.direction}-ct2-int8"
    if not model_dir.is_dir():
        parser.error(f"Model not found: {model_dir}. Run tools/setup_translation.py first.")
    translator = OpusTranslator(model_dir, intra_threads=args.threads)
    translated = translator.translate(args.text, beam_size=args.beam_size)
    if args.json_output:
        print(json.dumps({
            "direction": args.direction,
            "source": args.text,
            "translation": translated,
        }, ensure_ascii=False))
    else:
        print(translated)


if __name__ == "__main__":
    main()

