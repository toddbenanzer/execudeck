import tomllib
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

@dataclass
class Config:
    output_dir: str = "./output"
    template_path: str = "./template.pptx"
    prompts_dir: str = "./prompts"
    log_level: str = "INFO"

def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a TOML file. Fallback to default if not found."""
    config_path = Path(path) if path else Path("execudeck.toml")

    if not config_path.exists():
        if path: # Explicit path was provided but not found
            logger.warning(f"Config file not found at {config_path}. Using default configuration.")
        return Config()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        exec_data = data.get("execudeck", {})
        config = Config(
            output_dir=exec_data.get("output_dir", Config.output_dir),
            template_path=exec_data.get("template_path", Config.template_path),
            prompts_dir=exec_data.get("prompts_dir", Config.prompts_dir),
            log_level=exec_data.get("log_level", Config.log_level),
        )

        # Validate template_path existence, warn but do not error (as per requirement)
        if not Path(config.template_path).exists():
             logger.warning(f"Template path does not exist: {config.template_path}")

        return config
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Error parsing config file {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Unexpected error loading config {config_path}: {e}")
