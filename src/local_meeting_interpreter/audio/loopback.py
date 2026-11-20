from __future__ import annotations

import pyaudiowpatch as pyaudio


class LoopbackRecorder:
    def __init__(self, device_index: int, callback) -> None:
        self.audio = pyaudio.PyAudio()
        device = next(device for device in self.audio.get_loopback_device_info_generator() if int(device["index"]) == device_index)
        self.channels = int(device["maxInputChannels"])
        self.rate = int(device["defaultSampleRate"])
        self.frames_per_buffer = self.rate // 10
        self.stream = self.audio.open(
            format=pyaudio.paInt16, channels=self.channels, rate=self.rate,
            input=True, input_device_index=device_index,
            frames_per_buffer=self.frames_per_buffer, stream_callback=callback,
        )
