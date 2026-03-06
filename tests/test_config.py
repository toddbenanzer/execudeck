import pytest
import tempfile
import logging
from pathlib import Path
from execudeck.config import load_config, Config, ConfigError

def test_config_loads_toml(tmp_path):
    config_file = tmp_path / "execudeck.toml"
    config_file.write_text("""
[execudeck]
output_dir = "/custom/output"
template_path = "/custom/template.pptx"
prompts_dir = "/custom/prompts"
log_level = "DEBUG"
""")

    config = load_config(config_file)
    assert config.output_dir == "/custom/output"
    assert config.template_path == "/custom/template.pptx"
    assert config.prompts_dir == "/custom/prompts"
    assert config.log_level == "DEBUG"

def test_config_missing_file_uses_defaults():
    # Load from a non-existent path
    config = load_config("nonexistent_config.toml")
    assert config.output_dir == "./output"
    assert config.template_path == "./template.pptx"
    assert config.prompts_dir == "./prompts"
    assert config.log_level == "INFO"

def test_config_invalid_toml_raises(tmp_path):
    config_file = tmp_path / "bad.toml"
    config_file.write_text("[execudeck]\nbad_syntax")

    with pytest.raises(ConfigError):
        load_config(config_file)

def test_config_invalid_template_path_warns(tmp_path, caplog):
    config_file = tmp_path / "execudeck.toml"
    config_file.write_text("""
[execudeck]
template_path = "/this/does/not/exist.pptx"
""")

    with caplog.at_level(logging.WARNING):
        config = load_config(config_file)

    assert config.template_path == "/this/does/not/exist.pptx"
    assert "Template path does not exist: /this/does/not/exist.pptx" in caplog.text
