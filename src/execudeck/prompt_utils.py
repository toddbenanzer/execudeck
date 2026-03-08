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

import logging
logger = logging.getLogger(__name__)

def load_best_practices(path: str | Path = "best_practices.md") -> str:
    """Load the best practices content from disk safely."""
    best_practices_path = Path(path)
    if best_practices_path.exists():
        return best_practices_path.read_text()
    else:
        logger.warning(f"{path} not found. Proceeding without it.")
        return ""

def print_next_steps(prompt_path: str | Path, output_dir: str | Path, expected_json: str):
    """Print standard instructions for the next phase in the CLI."""
    print(f"\nNEXT STEPS:")
    print(f"1. Open {prompt_path}")
    print(f"2. Copy the full contents and paste into your LLM (Copilot, Gemini, etc.)")
    print(f"3. Save the LLM's JSON response to a file, e.g. {output_dir}/{expected_json}")
    print(f"4. Run: execudeck build {output_dir}/{expected_json}\n")

def finalize_prompt(prompt: str, output_dir: str | Path, prompt_filename: str, expected_json: str) -> Path:
    """Save the prompt to disk and print the next steps."""
    import logging
    logger = logging.getLogger(__name__)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = output_dir / prompt_filename
    prompt_path.write_text(prompt)
    logger.info(f"Prompt saved: {prompt_path}")

    print_next_steps(prompt_path, output_dir, expected_json)

    return prompt_path
