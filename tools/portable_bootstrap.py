from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> None:
    package_root = Path(__file__).resolve().parents[1]
    source = package_root / "src"
    os.environ["PYTHONPATH"] = str(source)
    os.environ.pop("PYTHONHOME", None)
    runtime_root = Path(__file__).resolve().parent
    version_suffix = f"{sys.version_info.major}{sys.version_info.minor}"
    sys.path[:] = [
        str(source),
        str(runtime_root / f"python{version_suffix}.zip"),
        str(runtime_root),
        str(runtime_root / "Lib" / "site-packages"),
    ]
    from local_meeting_interpreter.qt_app import main

    main()


if __name__ == "__main__":
    main()
