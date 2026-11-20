from dataclasses import dataclass
from pathlib import Path
import av
import numpy as np
from faster_whisper import WhisperModel


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Transcript:
    language: str
    language_probability: float
    duration: float
    segments: tuple[TranscriptSegment, ...]

    @property
    def text(self) -> str:
        return " ".join(segment.text for segment in self.segments).strip()


class WhisperRecognizer:
    def __init__(
        self,
        model_dir: str | Path,
        *,
        cpu_threads: int = 4,
        num_workers: int = 1,
    ) -> None:
        self.model = WhisperModel(
            str(model_dir),
            device="cpu",
            compute_type="int8",
            cpu_threads=cpu_threads,
            num_workers=num_workers,
        )

    def transcribe(self, audio: str | Path | np.ndarray, *, language: str | None = None) -> Transcript:
        segments, info = self.model.transcribe(
            audio,
            language=language,
            task="transcribe",
            beam_size=1,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        transcript_segments = tuple(
            TranscriptSegment(segment.start, segment.end, segment.text.strip())
            for segment in segments
            if segment.text.strip()
        )
        return Transcript(
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            segments=transcript_segments,
        )


def read_mono_audio(path: str | Path, sample_rate: int = 16000) -> np.ndarray:
    samples = []
    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=sample_rate)
        for frame in container.decode(stream):
            for converted in resampler.resample(frame):
                samples.append(converted.to_ndarray().reshape(-1))
    if not samples:
        return np.empty(0, dtype=np.float32)
    pcm = np.concatenate(samples)
    return pcm.astype(np.float32) / 32768.0

