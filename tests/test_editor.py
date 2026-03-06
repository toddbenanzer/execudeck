import pytest
import json
from pathlib import Path
from execudeck.config import Config
from execudeck.editor import edit
from pydantic import ValidationError

def get_valid_critique():
    return {
        "overall_score": 85,
        "summary": "Good deck, needs minor tweaks.",
        "checklist": {
            "storyline": {"section_name": "Storyline", "passed": True, "details": "Clear flow."},
            "formatting": {"section_name": "Formatting", "passed": False, "details": "Inconsistent fonts."},
            "data_viz": {"section_name": "Data Viz", "passed": True, "details": "Good charts."},
            "action_titles": {"section_name": "Action Titles", "passed": True, "details": "Strong titles."}
        },
        "slide_scores": [
            {
                "slide_number": 1,
                "score": 90,
                "violations": []
            }
        ]
    }

def test_edit_creates_prompt_file(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    critique_json_path = tmp_path / "critique.json"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    critique_json_path.write_text(json.dumps(get_valid_critique()))
    config = Config(prompts_dir=None)
    prompt_path = edit(pptx_path, critique_json_path, output_dir, config)
    assert prompt_path.exists()
    assert prompt_path.name == "edit_prompt.txt"

def test_edit_prompt_contains_critique(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    critique_json_path = tmp_path / "critique.json"
    output_dir = tmp_path / "output"
    create_sample_pptx(pptx_path)
    critique_json_path.write_text(json.dumps(get_valid_critique()))
    config = Config(prompts_dir=None)
    prompt_path = edit(pptx_path, critique_json_path, output_dir, config)
    prompt_text = prompt_path.read_text()
    assert "Good deck, needs minor tweaks." in prompt_text
    assert "{CRITIQUE_JSON}" not in prompt_text
