import pytest
import json
from pathlib import Path
from execudeck.config import Config
from execudeck.generator import generate
from pydantic import ValidationError

def test_generate_creates_prompt_file(tmp_path):
    content_json_path = tmp_path / "content.json"
    output_dir = tmp_path / "output"
    valid_content = {
        "objective": "Test",
        "audience": "Test Audience",
        "content_slides": [
            {
                "key_message": "Test Message",
                "supporting_points": ["Point 1", "Point 2"]
            }
        ]
    }
    content_json_path.write_text(json.dumps(valid_content))
    config = Config(prompts_dir=None)
    prompt_path = generate(content_json_path, output_dir, config)
    assert prompt_path.exists()
    assert prompt_path.name == "generate_prompt.txt"
    prompt_text = prompt_path.read_text()
    assert "You are an expert executive presentation creator" in prompt_text
    assert "Test Message" in prompt_text

def test_generate_validates_content_input(tmp_path):
    content_json_path = tmp_path / "content.json"
    output_dir = tmp_path / "output"
    invalid_content = {
        "objective": "Test",
        # Missing audience
        "content_slides": []
    }
    content_json_path.write_text(json.dumps(invalid_content))
    config = Config(prompts_dir=None)
    with pytest.raises(ValidationError):
        generate(content_json_path, output_dir, config)
