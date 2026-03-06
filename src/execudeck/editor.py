import json
import logging
from pathlib import Path
from execudeck.config import Config
from execudeck.extractor import extract
from execudeck.prompt_utils import load_prompt, fill_prompt
from execudeck.schema import CritiqueReport, DeckStructure

logger = logging.getLogger(__name__)

def edit(pptx_path: str | Path, critique_json_path: str | Path, output_dir: str | Path, config: Config) -> Path:
    """Orchestrate the edit mode: extract deck, validate critique, generate prompt."""
    pptx_path = Path(pptx_path)
    critique_json_path = Path(critique_json_path)
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

    # 4. Validate critique
    logger.info(f"Validating {critique_json_path}...")
    if not critique_json_path.exists():
        raise FileNotFoundError(f"Critique JSON not found: {critique_json_path}")

    critique_data = json.loads(critique_json_path.read_text())
    critique = CritiqueReport(**critique_data)

    # 5. Load prompt template and best practices
    template = load_prompt("edit", overrides_dir=config.prompts_dir)

    best_practices_path = Path("best_practices.md")
    best_practices = ""
    if best_practices_path.exists():
        best_practices = best_practices_path.read_text()
    else:
        logger.warning(f"best_practices.md not found. Proceeding without it.")

    deck_structure_schema = DeckStructure.model_json_schema()

    # 6. Fill prompt
    prompt = fill_prompt(
        template,
        BEST_PRACTICES=best_practices,
        DECK_JSON=deck_json,
        CRITIQUE_JSON=critique.model_dump_json(indent=2),
        DECK_STRUCTURE_SCHEMA=json.dumps(deck_structure_schema, indent=2)
    )

    # 7. Save prompt
    prompt_path = output_dir / "edit_prompt.txt"
    prompt_path.write_text(prompt)
    logger.info(f"Edit prompt saved: {prompt_path}")

    # 8. Print instructions
    print(f"\nNEXT STEPS:")
    print(f"1. Open {prompt_path}")
    print(f"2. Copy the full contents and paste into your LLM (Copilot, Gemini, etc.)")
    print(f"3. Save the LLM's JSON response to a file, e.g. {output_dir}/deck_structure.json")
    print(f"4. Run: execudeck build {output_dir}/deck_structure.json\n")

    return prompt_path
