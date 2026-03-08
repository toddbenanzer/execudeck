import json
import logging
from pathlib import Path
from execudeck.config import Config
from execudeck.prompt_utils import load_prompt, fill_prompt, load_best_practices, finalize_prompt
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

    best_practices = load_best_practices()

    deck_structure_schema = DeckStructure.model_json_schema()

    # 4. Fill prompt
    prompt = fill_prompt(
        template,
        BEST_PRACTICES=best_practices,
        CONTENT_JSON=content.model_dump_json(indent=2),
        DECK_STRUCTURE_SCHEMA=json.dumps(deck_structure_schema, indent=2)
    )

    # 5. Save prompt and print instructions
    return finalize_prompt(prompt, output_dir, "generate_prompt.txt", "deck_structure.json")
