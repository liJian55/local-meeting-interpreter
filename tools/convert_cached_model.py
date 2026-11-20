import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Convert a downloaded OPUS-MT archive to INT8.")
    parser.add_argument("direction", choices=("zh-en", "en-zh"))
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output_dir = project_root / "models" / f"opus-mt-{args.direction}-ct2-int8"
    converter = project_root / ".venv" / "Scripts" / "ct2-opus-mt-converter.exe"
    with zipfile.ZipFile(archive) as model_zip:
        if model_zip.testzip() is not None:
            raise ValueError(f"Corrupt model archive: {archive}")
        with tempfile.TemporaryDirectory(prefix="opus-mt-", dir=project_root / "models") as temp_dir:
            source_dir = Path(temp_dir) / "source"
            model_zip.extractall(source_dir)
            subprocess.run(
                [
                    sys.executable,
                    str(converter),
                    "--model_dir",
                    str(source_dir),
                    "--output_dir",
                    str(output_dir),
                    "--quantization",
                    "int8",
                ],
                check=True,
            )
            for tokenizer_name in ("source.spm", "target.spm"):
                shutil.copy2(source_dir / tokenizer_name, output_dir / tokenizer_name)
            (output_dir / "model-source.txt").write_text(
                f"Official OPUS-MT archive: {archive.name}\n",
                encoding="utf-8",
            )
    print(f"Installed: {output_dir}")


if __name__ == "__main__":
    main()

