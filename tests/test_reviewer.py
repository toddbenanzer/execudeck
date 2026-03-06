import pytest
import json
from pathlib import Path
from execudeck.config import Config
from execudeck.reviewer import review


def test_review_creates_prompt_and_extraction(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    output_dir = tmp_path / "output"

    create_sample_pptx(pptx_path)

    config = Config(prompts_dir=None)

    prompt_path = review(pptx_path, output_dir, config)

    # Assertions
    assert prompt_path.exists()
    assert prompt_path.name == "review_prompt.txt"

    extraction_path = output_dir / "deck_extraction.json"
    assert extraction_path.exists()

    # Check prompt contents
    prompt_text = prompt_path.read_text()
    assert "You are an expert executive presentation reviewer" in prompt_text

    # Ensure best practices placeholder was filled (since best_practices.md exists in root, or at least it doesn't leave {BEST_PRACTICES} string literal)
    assert "{BEST_PRACTICES}" not in prompt_text

    # Ensure DECK_JSON is serialized properly
    assert "Hello, World!" in prompt_text
