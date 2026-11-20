from __future__ import annotations

from dataclasses import dataclass

import pyaudiowpatch as pyaudio


@dataclass(frozen=True)
class AudioSource:
    key: str
    label: str
    device_index: int
    feishu_only: bool = False


def available_sources() -> list[AudioSource]:
    audio = pyaudio.PyAudio()
    try:
        devices = list(audio.get_loopback_device_info_generator())
        if not devices:
            return []
        try:
            default_output = audio.get_default_output_device_info()
            default_name = default_output["name"]
            feishu_device = next(
                (device for device in devices if device["name"].startswith(default_name)), devices[0]
            )
        except (OSError, KeyError):
            feishu_device = devices[0]
        return [
            AudioSource("feishu", "飞书会议声音（默认播放设备）", int(feishu_device["index"])),
            *[
                AudioSource(
                    f"system-{device['index']}",
                    f"本机播放声音（{device['name'].removesuffix(' [Loopback]')}）",
                    int(device["index"]),
                )
                for device in devices
            ],
        ]
    finally:
        audio.terminate()
