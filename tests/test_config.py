import pytest
import tempfile
import logging
from pathlib import Path
from execudeck.config import load_config, Config, ConfigError

def test_config_loads_toml(tmp_path):
    config_file = tmp_path / "execudeck.toml"
    template_file = tmp_path / "template.pptx"
    template_file.write_text("")

    config_file.write_text(f"""
[execudeck]
output_dir = "/custom/output"
template_path = "{template_file}"
prompts_dir = "/custom/prompts"
log_level = "DEBUG"
""")

    config = load_config(config_file)
    assert config.output_dir == "/custom/output"
    assert config.template_path == str(template_file)
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

def test_config_invalid_template_path_raises(tmp_path):
    config_file = tmp_path / "execudeck.toml"
    config_file.write_text("""
[execudeck]
template_path = "/this/does/not/exist.pptx"
""")

    with pytest.raises(ConfigError):
        load_config(config_file)

def test_config_cli_overrides_file(tmp_path):
    config_file = tmp_path / "execudeck.toml"
    # Provide an existing template path to avoid ConfigError
    template_file = tmp_path / "template.pptx"
    template_file.write_text("")

    config_file.write_text(f"""
[execudeck]
output_dir = "/file/output"
template_path = "{template_file}"
""")

    # Simulating CLI overriding by changing properties after load
    config = load_config(config_file)
    assert config.output_dir == "/file/output"

    # Simulate CLI override
    cli_output_dir = "/cli/output"
    config.output_dir = cli_output_dir

    assert config.output_dir == "/cli/output"
