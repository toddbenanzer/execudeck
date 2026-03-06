import json
import logging
from pathlib import Path
from execudeck.config import Config
from execudeck.prompt_utils import load_prompt, fill_prompt
from execudeck.schema import ContentInput, DeckStructure

logger = logging.getLogger(__name__)

def generate(content_json_path: str | Path, output_dir: str | Path, config: Config) -> Path:
    """Orchestrate the generate mode: validate content, generate prompt."""
    content_json_path = Path(content_json_path)
    output_dir = Path(output_dir)

    # 1. Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Validate input content
    logger.info(f"Validating {content_json_path}...")
    if not content_json_path.exists():
        raise FileNotFoundError(f"Content JSON not found: {content_json_path}")

    content_data = json.loads(content_json_path.read_text())
    content = ContentInput(**content_data)

    # 3. Load prompt template and best practices
    template = load_prompt("generate", overrides_dir=config.prompts_dir)

    best_practices_path = Path("best_practices.md")
    best_practices = ""
    if best_practices_path.exists():
        best_practices = best_practices_path.read_text()
    else:
        logger.warning(f"best_practices.md not found. Proceeding without it.")

    deck_structure_schema = DeckStructure.model_json_schema()

    # 4. Fill prompt
    prompt = fill_prompt(
        template,
        BEST_PRACTICES=best_practices,
        CONTENT_JSON=content.model_dump_json(indent=2),
        DECK_STRUCTURE_SCHEMA=json.dumps(deck_structure_schema, indent=2)
    )

    # 5. Save prompt
    prompt_path = output_dir / "generate_prompt.txt"
    prompt_path.write_text(prompt)
    logger.info(f"Generate prompt saved: {prompt_path}")

    # 6. Print instructions
    print(f"\nNEXT STEPS:")
    print(f"1. Open {prompt_path}")
    print(f"2. Copy the full contents and paste into your LLM (Copilot, Gemini, etc.)")
    print(f"3. Save the LLM's JSON response to a file, e.g. {output_dir}/deck_structure.json")
    print(f"4. Run: execudeck build {output_dir}/deck_structure.json\n")

    return prompt_path
