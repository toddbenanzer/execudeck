import pytest
import json
from pathlib import Path
from execudeck.config import Config
from execudeck.editor import edit
from pydantic import ValidationError


def test_edit_creates_prompt_and_extraction(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    critique_json_path = tmp_path / "critique.json"
    output_dir = tmp_path / "output"

    create_sample_pptx(pptx_path)

    valid_critique = {
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

    critique_json_path.write_text(json.dumps(valid_critique))

    config = Config(prompts_dir=None)

    prompt_path = edit(pptx_path, critique_json_path, output_dir, config)

    # Assertions
    assert prompt_path.exists()
    assert prompt_path.name == "edit_prompt.txt"

    extraction_path = output_dir / "deck_extraction.json"
    assert extraction_path.exists()

    # Check prompt contents
    prompt_text = prompt_path.read_text()
    assert "You are an expert executive presentation creator" in prompt_text

    # Ensure DECK_JSON and CRITIQUE_JSON are serialized properly
    assert "Hello, World!" in prompt_text
    assert "Good deck, needs minor tweaks." in prompt_text

def test_edit_invalidates_critique_json(tmp_path, create_sample_pptx):
    pptx_path = tmp_path / "sample.pptx"
    critique_json_path = tmp_path / "critique.json"
    output_dir = tmp_path / "output"

    create_sample_pptx(pptx_path)

    invalid_critique = {
        "overall_score": 105, # Invalid score
        "summary": "Bad",
        "checklist": {
            "storyline": {"section_name": "Storyline", "passed": True, "details": "Clear flow."},
            "formatting": {"section_name": "Formatting", "passed": False, "details": "Inconsistent fonts."},
            "data_viz": {"section_name": "Data Viz", "passed": True, "details": "Good charts."},
            "action_titles": {"section_name": "Action Titles", "passed": True, "details": "Strong titles."}
        },
        "slide_scores": []
    }

    critique_json_path.write_text(json.dumps(invalid_critique))

    config = Config(prompts_dir=None)

    with pytest.raises(ValidationError):
        edit(pptx_path, critique_json_path, output_dir, config)
