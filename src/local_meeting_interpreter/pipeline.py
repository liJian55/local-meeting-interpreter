from dataclasses import asdict
from pathlib import Path

from local_meeting_interpreter.asr import WhisperRecognizer
from local_meeting_interpreter.asr.whisper import Transcript
from local_meeting_interpreter.translation import OpusTranslator


class OfflineInterpreter:
    def __init__(self, recognizer: WhisperRecognizer, model_root: str | Path) -> None:
        self.recognizer = recognizer
        self.model_root = Path(model_root)
        self.translators: dict[str, OpusTranslator] = {}

    def transcribe_and_translate(self, audio_path: str | Path) -> tuple[Transcript, list[dict]]:
        transcript = self.recognizer.transcribe(audio_path)
        if transcript.language not in ("zh", "en"):
            raise ValueError(f"Unsupported meeting language: {transcript.language}")
        direction = "zh-en" if transcript.language == "zh" else "en-zh"
        translator = self.translators.get(direction)
        if translator is None:
            translator = OpusTranslator(self.model_root / f"opus-mt-{direction}-ct2-int8")
            self.translators[direction] = translator
        segments = []
        for segment in transcript.segments:
            translated = translator.translate(segment.text)
            segments.append({
                **asdict(segment),
                "language": transcript.language,
                "translation": translated,
            })
        return transcript, segments

