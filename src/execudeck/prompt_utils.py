from pathlib import Path

def load_prompt(template_name: str, overrides_dir: str | Path | None = None) -> str:
    """Load a prompt template from disk, with optional override directory."""
    if overrides_dir:
        override_path = Path(overrides_dir) / f"{template_name}.txt"
        if override_path.exists():
            return override_path.read_text()

    # Default path inside package
    default_path = Path(__file__).parent / "prompts" / f"{template_name}.txt"
    if not default_path.exists():
        raise FileNotFoundError(f"Prompt template {template_name}.txt not found.")

    return default_path.read_text()

def fill_prompt(template: str, **kwargs) -> str:
    """Fill the placeholders in the prompt template."""
    return template.format(**kwargs)
