from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np

from local_meeting_interpreter.asr import WhisperRecognizer
from local_meeting_interpreter.audio.capture_process import CaptureProcess
from local_meeting_interpreter.translation import OpusTranslator


class RealtimeInterpreter:
    def __init__(
        self,
        model_root,
        on_segment: Callable[[str, str, str], None],
        on_status: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.model_root = Path(model_root)
        self.on_segment = on_segment
        self.on_status = on_status
        self.on_error = on_error
        self.stopping = threading.Event()
        self.recorder: CaptureProcess | None = None

    def stop(self) -> None:
        self.stopping.set()
        if self.recorder:
            self.recorder.request_stop()

    def run(
        self, english_to_chinese: bool, chinese_to_english: bool,
        device_index: int, feishu_only: bool
    ) -> None:
        try:
            self.on_status("正在加载本地识别模型...")
            recognizer = WhisperRecognizer(self.model_root / "faster-whisper-small", cpu_threads=4)
            translators = {}
            if english_to_chinese:
                translators["en"] = OpusTranslator(self.model_root / "opus-mt-en-zh-ct2-int8")
            if chinese_to_english:
                translators["zh"] = OpusTranslator(self.model_root / "opus-mt-zh-en-ct2-int8")
            if feishu_only:
                self.recorder = CaptureProcess(device_index)
                self.on_status("正在监听飞书会议输出，请避免同时播放其他音频。")
            else:
                self.recorder = CaptureProcess(device_index)
                self.on_status("正在监听本机播放声音。")
            buffer = np.empty(0, dtype=np.float32)
            silence = 0.0
            recent_texts: list[str] = []
            for chunk in self.recorder.chunks():
                if self.stopping.is_set():
                    break
                buffer = np.concatenate((buffer, chunk))
                loud = float(np.sqrt(np.mean(np.square(chunk)))) > 0.008
                silence = 0.0 if loud else silence + len(chunk) / 16000
                if len(buffer) < 16000:
                    continue
                if silence < 0.5 and len(buffer) < 16000 * 10:
                    continue
                audio, buffer = buffer, np.empty(0, dtype=np.float32)
                silence = 0.0
                if len(audio) < 16000:
                    continue
                transcript = recognizer.transcribe(audio)
                for segment in transcript.segments:
                    text = segment.text.strip()
                    normalized = "".join(text.lower().split())
                    if not normalized or normalized in recent_texts:
                        continue
                    recent_texts = (recent_texts + [normalized])[-12:]
                    translator = translators.get(transcript.language)
                    if translator:
                        self.on_segment(transcript.language, text, translator.translate(text))
                    else:
                        self.on_segment(transcript.language, text, "此翻译方向未开启")
        except Exception as error:
            if not self.stopping.is_set():
                self.on_error(str(error))
        finally:
            if self.recorder:
                self.recorder.close()
            self.on_status("同传已停止，软件保持打开。")
