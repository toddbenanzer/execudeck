import pytest
from pathlib import Path
from execudeck.prompt_utils import load_prompt, fill_prompt

def test_load_prompt_default():
    content = load_prompt("review")
    assert "You are an expert executive presentation reviewer" in content

def test_load_prompt_override(tmp_path):
    override_dir = tmp_path / "prompts"
    override_dir.mkdir()
    (override_dir / "review.txt").write_text("Override review prompt")

    content = load_prompt("review", overrides_dir=override_dir)
    assert content == "Override review prompt"

def test_load_prompt_missing():
    with pytest.raises(FileNotFoundError):
        load_prompt("missing")

def test_fill_prompt():
    template = "Hello {name}, your score is {score}"
    filled = fill_prompt(template, name="Alice", score="100")
    assert filled == "Hello Alice, your score is 100"

def test_fill_prompt_missing_kwargs():
    template = "Hello {name}"
    with pytest.raises(KeyError):
        fill_prompt(template)
