from __future__ import annotations

import argparse
import sys
import time

import pyaudiowpatch as pyaudio

from local_meeting_interpreter.audio.loopback import LoopbackRecorder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("device_index", type=int)
    args = parser.parse_args()
    def receive(data, frame_count, time_info, status):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        return None, pyaudio.paContinue

    recorder = LoopbackRecorder(args.device_index, receive)
    print(f"READY {recorder.rate} {recorder.channels}", file=sys.stderr, flush=True)
    while recorder.stream.is_active():
        time.sleep(0.1)


if __name__ == "__main__":
    main()
