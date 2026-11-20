from pathlib import Path

import pytest

from local_meeting_interpreter.translation import OpusTranslator


MODEL_ROOT = Path(__file__).resolve().parents[1] / "models"


@pytest.mark.parametrize("direction", ["zh-en", "en-zh"])
def test_installed_model_translates_offline(direction: str) -> None:
    model_dir = MODEL_ROOT / f"opus-mt-{direction}-ct2-int8"
    if not model_dir.is_dir():
        pytest.skip(f"Model not installed: {model_dir}")
    translator = OpusTranslator(model_dir)
    source = "我们明天讨论发布计划。" if direction == "zh-en" else "We will discuss the release plan tomorrow."
    assert translator.translate(source).strip()
    assert translator.translate("") == ""

