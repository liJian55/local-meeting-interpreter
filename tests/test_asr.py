import sys
from pathlib import Path

import numpy as np
import pytest

from local_meeting_interpreter.asr.whisper import WhisperRecognizer, read_mono_audio


MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "faster-whisper-small"


def test_decode_generated_audio() -> None:
    sample_path = Path(__file__).resolve().parents[1] / "samples" / "meeting-en.wav"
    if not sample_path.is_file():
        pytest.skip("Generated audio sample is not available")
    audio = read_mono_audio(sample_path)
    assert audio.dtype == np.float32
    assert len(audio) > 16000
    assert np.max(np.abs(audio)) > 0.01


def test_transcribe_generated_english_sample() -> None:
    if not (MODEL_DIR / "model.bin").is_file():
        pytest.skip("Whisper model not installed")
    sample_path = Path(__file__).resolve().parents[1] / "samples" / "meeting-en.wav"
    if not sample_path.is_file():
        pytest.skip("Generated audio sample is not available")
    if sys.platform != "win32":
        pytest.skip("This smoke test is intended for the local Windows environment")
    transcript = WhisperRecognizer(MODEL_DIR).transcribe(sample_path, language="en")
    assert transcript.language == "en"
    assert "flight" in transcript.text.lower()
    assert transcript.segments

