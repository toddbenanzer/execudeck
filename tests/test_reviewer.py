import pytest
import json
from pathlib import Path
from execudeck.config import Config
from execudeck.reviewer import review

def test_review_creates_prompt_file(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    config = Config(prompts_dir=None)
    prompt_path = review(pptx_path, output_dir, config)
    assert prompt_path.exists()
    assert prompt_path.name == "review_prompt.txt"

def test_review_creates_extraction_json(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    config = Config(prompts_dir=None)
    review(pptx_path, output_dir, config)
    extraction_path = output_dir / "deck_extraction.json"
    assert extraction_path.exists()

def test_review_prompt_contains_best_practices(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    config = Config(prompts_dir=None)
    prompt_path = review(pptx_path, output_dir, config)
    prompt_text = prompt_path.read_text()
    assert "{BEST_PRACTICES}" not in prompt_text

def test_review_prompt_contains_deck_json(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    config = Config(prompts_dir=None)
    prompt_path = review(pptx_path, output_dir, config)
    prompt_text = prompt_path.read_text()
    assert "{DECK_JSON}" not in prompt_text
    assert "Hello, World!" in prompt_text
