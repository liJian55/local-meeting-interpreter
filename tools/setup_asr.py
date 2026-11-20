import shutil
import subprocess
import sys
from pathlib import Path


FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "models" / "faster-whisper-small"
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = "https://huggingface.co/Systran/faster-whisper-small/resolve/main"
    for filename in FILES:
        destination = output_dir / filename
        if destination.exists():
            print(f"Already downloaded: {destination}", flush=True)
            continue
        partial = destination.with_suffix(destination.suffix + ".part")
        subprocess.run(
            [
                "curl.exe" if sys.platform == "win32" else "curl",
                "-L",
                "--fail",
                "--retry",
                "2",
                "-C",
                "-",
                "-o",
                str(partial),
                f"{base_url}/{filename}",
            ],
            check=True,
        )
        shutil.move(partial, destination)
        print(f"Downloaded: {destination}", flush=True)


if __name__ == "__main__":
    main()

