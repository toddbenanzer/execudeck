import json
import logging
from pathlib import Path
from execudeck.config import Config
from execudeck.extractor import extract
from execudeck.prompt_utils import load_prompt, fill_prompt, load_best_practices, finalize_prompt
from execudeck.schema import CritiqueReport

logger = logging.getLogger(__name__)

def review(pptx_path: str | Path, output_dir: str | Path, config: Config) -> Path:
    """Orchestrate the review mode: extract deck, generate prompt."""
    pptx_path = Path(pptx_path)
    output_dir = Path(output_dir)

    # 1. Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Extract deck
    logger.info(f"Extracting {pptx_path}...")
    deck = extract(pptx_path)
    deck_json = deck.model_dump_json(indent=2)

    # 3. Save extracted deck to output dir
    extraction_path = output_dir / "deck_extraction.json"
    extraction_path.write_text(deck_json)
    logger.info(f"Deck extracted: {extraction_path}")

    # 4. Load prompt template and best practices
    template = load_prompt("review", overrides_dir=config.prompts_dir)

    best_practices = load_best_practices()

    critique_schema = CritiqueReport.model_json_schema()

    # 5. Fill prompt
    prompt = fill_prompt(
        template,
        BEST_PRACTICES=best_practices,
        DECK_JSON=deck_json,
        CRITIQUE_SCHEMA=json.dumps(critique_schema, indent=2)
    )

    # 6. Save prompt and print instructions
    return finalize_prompt(prompt, output_dir, "review_prompt.txt", "critique.json")
