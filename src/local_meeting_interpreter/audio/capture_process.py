from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from local_meeting_interpreter.paths import project_root


def console_python() -> str:
    executable = str(Path(sys.executable))
    if executable.lower().endswith("pythonw.exe"):
        executable = str(Path(executable).with_name("python.exe"))
    if not Path(executable).is_file():
        raise RuntimeError(f"找不到音频采集运行环境：{executable}")
    return executable


def capture_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root() / "src")
    environment.pop("PYTHONHOME", None)
    if (project_root() / "runtime" / "python.exe").is_file():
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
    return environment


class CaptureProcess:
    def __init__(self, device_index: int) -> None:
        environment = capture_environment()
        self.process = subprocess.Popen(
            [console_python(), "-u", "-m", "local_meeting_interpreter.audio.capture_worker", str(device_index)],
            cwd=project_root(), env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.rate = 48000
        self.channels = 2
        self.queue: queue.Queue[bytes | None] = queue.Queue(maxsize=50)
        self.reader = threading.Thread(target=self._read_audio, daemon=True)
        self.reader.start()
        self.error_reader = threading.Thread(target=self._read_errors, daemon=True)
        self.error_reader.start()
        self.errors: list[str] = []

    def _read_audio(self) -> None:
        assert self.process.stdout is not None
        try:
            while True:
                data = self.process.stdout.read(self.rate // 10 * self.channels * 2)
                if not data:
                    break
                self.queue.put(data)
        except (OSError, ValueError):
            pass
        finally:
            self.queue.put(None)

    def chunks(self) -> Iterator[np.ndarray]:
        while True:
            try:
                data = self.queue.get(timeout=0.1)
            except queue.Empty:
                if self.process.poll() is not None:
                    break
                continue
            if data is None:
                break
            samples = np.frombuffer(data, dtype=np.int16).reshape(-1, self.channels)
            mono = samples.mean(axis=1).astype(np.float32) / 32768.0
            yield mono[::3].copy()
        if self.process.poll() not in (0, None, 1, -1):
            raise RuntimeError("\n".join(self.errors) or "音频采集进程异常退出")

    def _read_errors(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.errors.append(line.decode("utf-8", errors="replace").rstrip())

    def request_stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()

    def close(self) -> None:
        self.request_stop()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        if self.process.stdout:
            self.process.stdout.close()
