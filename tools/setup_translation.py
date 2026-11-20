import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


MODELS = {
    "zh-en": "https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip",
    "en-zh": "https://object.pouta.csc.fi/Tatoeba-MT-models/eng-zho/opus-2020-07-17.zip",
}


def install_model(direction: str, model_root: Path, converter: Path, force: bool) -> None:
    output_dir = model_root / f"opus-mt-{direction}-ct2-int8"
    if output_dir.exists():
        if not force:
            print(f"Already installed: {output_dir}", flush=True)
            return
        resolved_output = output_dir.resolve()
        if resolved_output.parent != model_root.resolve() or resolved_output.name != f"opus-mt-{direction}-ct2-int8":
            raise ValueError(f"Unexpected model output directory: {resolved_output}")
        shutil.rmtree(resolved_output)

    model_root.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="opus-mt-", dir=model_root) as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "model.zip"
        print(f"Downloading {MODELS[direction]}", flush=True)
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
                str(archive_path),
                MODELS[direction],
            ],
            check=True,
        )
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temp_path / "source")
        subprocess.run(
            [
                sys.executable,
                str(converter),
                "--model_dir",
                str(temp_path / "source"),
                "--output_dir",
                str(output_dir),
                "--quantization",
                "int8",
            ],
            check=True,
        )
        for tokenizer_name in ("source.spm", "target.spm"):
            shutil.copy2(temp_path / "source" / tokenizer_name, output_dir / tokenizer_name)
        (output_dir / "model-source.txt").write_text(
            f"Official OPUS-MT archive: {MODELS[direction]}\n",
            encoding="utf-8",
        )
    print(f"Installed: {output_dir}", flush=True)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Install OPUS-MT models for offline use.")
    parser.add_argument("--direction", choices=(*MODELS, "both"), default="both")
    parser.add_argument("--model-root", type=Path, default=project_root / "models")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    converter = project_root / ".venv" / "Scripts" / "ct2-opus-mt-converter.exe"
    if not converter.is_file():
        parser.error(f"Converter not found: {converter}. Install the project first.")
    directions = MODELS if args.direction == "both" else (args.direction,)
    for direction in directions:
        install_model(direction, args.model_root.resolve(), converter, args.force)


if __name__ == "__main__":
    main()

