# execudeck — Implementation Plan

A Python package for reviewing, generating, and editing executive PowerPoint
presentations. The package operates as a **two-phase, human-in-the-loop tool**:
Phase 1 serializes decks and generates prompts for the user to paste into a
manual LLM tool (Microsoft Copilot, Google Gemini, etc.); Phase 2 consumes the
LLM's JSON response and builds or edits the `.pptx` file.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Structure](#2-repository-structure)
3. [Phase 1 — Extract & Prompt Generation](#3-phase-1--extract--prompt-generation)
4. [Phase 2 — Build (JSON → .pptx)](#4-phase-2--build-json--pptx)
5. [JSON Schemas](#5-json-schemas)
6. [Prompt Templates](#6-prompt-templates)
7. [CLI Design](#7-cli-design)
8. [Configuration](#8-configuration)
9. [Python Library API](#9-python-library-api)
10. [Dependencies & Package Metadata](#10-dependencies--package-metadata)
11. [Testing Plan](#11-testing-plan)
12. [Implementation Task Checklist](#12-implementation-task-checklist)

---

## 1. Architecture Overview

### Two-Phase Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1 — Extract & Prompt Generation                         │
│                                                                 │
│  review mode:   .pptx ──► extractor ──► deck JSON              │
│                                            │                   │
│  generate mode: content.json ──────────────┤                   │
│                                            ▼                   │
│  edit mode:     .pptx + critique.json ──► prompt builder       │
│                                            │                   │
│                                            ▼                   │
│                                     prompt.txt (saved to disk) │
│                                            │                   │
│                                    [USER copies prompt into    │
│                                     Copilot / Gemini / etc.]   │
│                                            │                   │
│                                    [USER saves LLM response    │
│                                     as JSON file to disk]      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2 — Build                                                │
│                                                                 │
│  critique.json (review output) ──► saved report, no .pptx      │
│                                                                 │
│  deck_structure.json (generate/edit output)                     │
│        │                                                        │
│        ▼                                                        │
│  Pydantic validation ──► python-pptx builder                   │
│        │                       │                               │
│        ▼                       ▼                               │
│  clear error msgs       output.pptx (written to output dir)    │
└─────────────────────────────────────────────────────────────────┘
```

### Three Operation Modes

| Mode | Phase 1 Input | Phase 1 Output | LLM Returns | Phase 2 Output |
|---|---|---|---|---|
| **review** | `.pptx` file | `review_prompt.txt` + `deck_extraction.json` | `critique.json` | Structured review report (no `.pptx`) |
| **generate** | `content.json` | `generate_prompt.txt` | `deck_structure.json` | `output.pptx` |
| **edit** | `.pptx` + `critique.json` | `edit_prompt.txt` + `deck_extraction.json` | `deck_structure.json` | `output.pptx` |

---

## 2. Repository Structure

```
execudeck/
├── pyproject.toml                  # Package metadata, build system, dependencies
├── execudeck.toml                  # Default project-level config (user editable)
├── best_practices.md               # MBB/banking standards reference (already exists)
├── README.md
│
├── src/
│   └── execudeck/
│       ├── __init__.py             # Public API exports
│       ├── cli.py                  # Click CLI: review, generate, edit, build
│       ├── config.py               # Config loading from execudeck.toml
│       ├── extractor.py            # .pptx → deck extraction JSON
│       ├── builder.py              # deck_structure JSON → .pptx
│       ├── reviewer.py             # Orchestrates review mode (Phase 1)
│       ├── generator.py            # Orchestrates generate mode (Phase 1)
│       ├── editor.py               # Orchestrates edit mode (Phase 1)
│       │
│       ├── schema/
│       │   ├── __init__.py
│       │   ├── extraction.py       # Pydantic models: extracted deck representation
│       │   ├── critique.py         # Pydantic models: LLM critique/review output
│       │   └── deck_structure.py   # Pydantic models: LLM deck generation output
│       │
│       └── prompts/
│           ├── review.txt          # Review mode prompt template
│           ├── generate.txt        # Generate mode prompt template
│           └── edit.txt            # Edit mode prompt template
│
└── tests/
    ├── conftest.py                 # Shared fixtures (sample .pptx, sample JSONs)
    ├── test_extractor.py
    ├── test_builder.py
    ├── test_reviewer.py
    ├── test_generator.py
    ├── test_editor.py
    ├── test_schema_extraction.py
    ├── test_schema_critique.py
    ├── test_schema_deck_structure.py
    ├── test_config.py
    └── test_cli.py
```

---

## 3. Phase 1 — Extract & Prompt Generation

### 3.1 Extractor (`extractor.py`)

Responsibility: read a `.pptx` file and serialize its full content into a
structured `DeckExtraction` JSON.

**Data captured per slide:**

- `slide_number` (int, 1-indexed)
- `layout_name` (str — the PowerPoint layout name, e.g. "Title Slide")
- `title` (str — raw text of the title placeholder)
- `subtitle` (str — raw text of the subtitle placeholder, if present)
- `body_shapes` — list of all text frames on the slide:
  - `shape_name` (str)
  - `shape_type` (str — "TEXT_BOX", "PLACEHOLDER", etc.)
  - `paragraphs` — list of paragraphs, each with:
    - `text` (str)
    - `level` (int — outline indent level, 0 = top)
    - `bold` (bool)
    - `italic` (bool)
    - `font_size` (float | null — in points)
    - `font_name` (str | null)
    - `color_rgb` (str | null — hex, e.g. "#0070C0")
- `charts` — list of charts on the slide:
  - `shape_name` (str)
  - `chart_type` (str — python-pptx ChartType enum name)
  - `title` (str | null)
  - `series` — list of `{ name, values: [] }`
  - `categories` (list[str])
- `images` — list of `{ shape_name, description: null }` (images cannot be
  serialized to text; note their presence only)
- `tables` — list of tables:
  - `shape_name` (str)
  - `rows` — list of lists of cell text strings
- `footnotes` — text from footer placeholder or small-font text boxes at
  bottom of slide (detected heuristically: font size ≤ 12pt, positioned in
  bottom 15% of slide)
- `speaker_notes` (str — notes pane text)
- `slide_dimensions` — `{ width_emu, height_emu }` (from slide layout)
- `background_color` (str | null — hex of solid background fill, if set)

**Deck-level metadata captured:**

- `title` — from core properties
- `author` — from core properties
- `slide_count` (int)
- `slide_width_emu` (int)
- `slide_height_emu` (int)
- `theme_fonts` — `{ major, minor }` from theme XML
- `theme_colors` — dict of theme color roles → hex values

**Implementation notes:**

- Use `python-pptx`'s `Presentation`, `Slide`, `Shape`, `TextFrame` APIs
- Iterate `prs.slides` for slides; `slide.shapes` for shapes
- Use `shape.has_chart`, `shape.has_table`, `shape.has_text_frame` guards
- Extract notes via `slide.notes_slide.notes_text_frame.text`
- Parse theme XML via `prs.core_properties` and `prs.slide_master.theme_color_map`
- Output serialized as `DeckExtraction` Pydantic model → `.model_dump()` → JSON

### 3.2 Reviewer (`reviewer.py`)

Responsibility: orchestrate the review phase.

**Steps:**

1. Call `extractor.extract(pptx_path)` → `DeckExtraction`
2. Serialize `DeckExtraction` to JSON string
3. Load review prompt template from `prompts/review.txt`
4. Inject into template:
   - `{BEST_PRACTICES}` — full content of `best_practices.md`
   - `{DECK_JSON}` — the serialized `DeckExtraction` JSON
   - `{CRITIQUE_SCHEMA}` — the `CritiqueReport` JSON schema (from Pydantic)
5. Write filled prompt to `<output_dir>/review_prompt.txt`
6. Write `DeckExtraction` JSON to `<output_dir>/deck_extraction.json`
7. Print instructions to terminal: where the files were saved, what the user
   should do next (copy prompt → paste into LLM → save response as JSON)

### 3.3 Generator (`generator.py`)

Responsibility: orchestrate the generate phase.

**Steps:**

1. Load and validate `content.json` against `ContentInput` Pydantic model
2. Serialize to JSON string
3. Load generate prompt template from `prompts/generate.txt`
4. Inject into template:
   - `{BEST_PRACTICES}` — full content of `best_practices.md`
   - `{CONTENT_JSON}` — the serialized `ContentInput` JSON
   - `{DECK_STRUCTURE_SCHEMA}` — the `DeckStructure` JSON schema
5. Write filled prompt to `<output_dir>/generate_prompt.txt`
6. Print instructions to terminal

### 3.4 Editor (`editor.py`)

Responsibility: orchestrate the edit phase.

**Steps:**

1. Call `extractor.extract(pptx_path)` → `DeckExtraction`
2. Load and validate `critique.json` against `CritiqueReport` Pydantic model
3. Serialize both to JSON strings
4. Load edit prompt template from `prompts/edit.txt`
5. Inject into template:
   - `{BEST_PRACTICES}` — full content of `best_practices.md`
   - `{DECK_JSON}` — the serialized `DeckExtraction` JSON
   - `{CRITIQUE_JSON}` — the serialized `CritiqueReport` JSON
   - `{DECK_STRUCTURE_SCHEMA}` — the `DeckStructure` JSON schema
6. Write filled prompt to `<output_dir>/edit_prompt.txt`
7. Write `DeckExtraction` JSON to `<output_dir>/deck_extraction.json`
8. Print instructions to terminal

---

## 4. Phase 2 — Build (JSON → .pptx)

### 4.1 Builder (`builder.py`)

Responsibility: take a validated `DeckStructure` JSON and produce a `.pptx`
file using the user-supplied template.

**Steps:**

1. Load and validate `deck_structure.json` against `DeckStructure` Pydantic model
   - On validation failure: print field-level error messages with clear descriptions;
     exit with non-zero code
2. Load the template `.pptx` from `config.template_path`
   - If no template specified: create a new blank `Presentation()`
3. For each `Slide` in `deck_structure.slides`:
   a. **Select slide layout** from template based on `slide.layout` field
      - Supported layouts: `title_slide`, `exec_summary`, `data_slide`,
        `section_divider`, `blank`, `appendix`
      - Map layout names to template slide layout indices via a config mapping
   b. **Add slide** to the presentation: `prs.slides.add_slide(layout)`
   c. **Set action title**: find title placeholder → set `.text` → apply font
      size from template (do not override)
   d. **Set subtitle**: find subtitle placeholder → set `.text` (if present on layout)
   e. **Add body bullets**: find body placeholder → iterate `slide.body.bullets`:
      - Set `paragraph.text`, `paragraph.level`
      - Apply `bold` via `paragraph.runs[0].font.bold`
      - Preserve bullet indentation levels
   f. **Add chart** (if `slide.chart` is not null):
      - Create `ChartData` object with categories and series values
      - Use `slide.shapes.add_chart(chart_type, left, top, width, height, chart_data)`
      - Map `slide.chart.type` string to `XL_CHART_TYPE` enum
      - Configure chart:
        - Set chart title from `slide.chart.title`
        - Set axis labels from `x_axis.label` and `y_axis.label`
        - Enforce `y_axis.start_at_zero = True` for bar charts regardless of JSON
        - Apply series colors from `slide.chart.series[n].color` (hex → RGBColor)
        - Remove gridlines, 3D effects, and chart border (enforce Tufte rules)
        - Add data labels directly on series (remove legend if direct labels present)
        - Apply annotations as text boxes positioned near annotated data points
   g. **Add footnotes**: create a text box at bottom of slide with small font;
      join footnote strings with `" | "` separator
   h. **Set speaker notes**: `slide.notes_slide.notes_text_frame.text = notes`
   i. **Add page number**: insert slide number placeholder or text box in
      bottom-right corner using `slide_number` value
4. **Enforce deck-level consistency** post-build:
   - Verify title placeholder position is identical across all slides
   - Log a warning if any slide title position deviates (builder cannot fix
     Slide Master issues — user must fix template)
5. Save output `.pptx` to `<output_dir>/<stem>_execudeck.pptx`
6. Print success message with output path

**Supported chart types (mapping from JSON string → XL_CHART_TYPE):**

| JSON `type` value | python-pptx constant |
|---|---|
| `"bar"` | `XL_CHART_TYPE.COLUMN_CLUSTERED` |
| `"horizontal_bar"` | `XL_CHART_TYPE.BAR_CLUSTERED` |
| `"stacked_bar"` | `XL_CHART_TYPE.COLUMN_STACKED` |
| `"line"` | `XL_CHART_TYPE.LINE` |
| `"pie"` | `XL_CHART_TYPE.PIE` |
| `"donut"` | `XL_CHART_TYPE.DOUGHNUT` |
| `"scatter"` | `XL_CHART_TYPE.XY_SCATTER` |
| `"waterfall"` | `XL_CHART_TYPE.COLUMN_STACKED` (with floating bars) |
| `"area"` | `XL_CHART_TYPE.AREA` |

Note: True waterfall charts are not natively supported in python-pptx;
implement as a stacked column chart with an invisible base series.

---

## 5. JSON Schemas

### 5.1 DeckExtraction Schema (`schema/extraction.py`)

Represents the full serialization of an existing `.pptx` for LLM input.

```
DeckExtraction
├── version: str                    # Schema version, e.g. "1.0"
├── metadata: DeckMetadata
│   ├── title: str | None
│   ├── author: str | None
│   ├── slide_count: int
│   ├── slide_width_emu: int
│   ├── slide_height_emu: int
│   ├── theme_fonts: ThemeFonts
│   │   ├── major: str | None
│   │   └── minor: str | None
│   └── theme_colors: dict[str, str]   # role → hex
├── slides: list[ExtractedSlide]
    ├── slide_number: int
    ├── layout_name: str
    ├── title: str | None
    ├── subtitle: str | None
    ├── body_shapes: list[ExtractedShape]
    │   ├── shape_name: str
    │   ├── shape_type: str
    │   └── paragraphs: list[ExtractedParagraph]
    │       ├── text: str
    │       ├── level: int
    │       ├── bold: bool
    │       ├── italic: bool
    │       ├── font_size: float | None
    │       ├── font_name: str | None
    │       └── color_rgb: str | None
    ├── charts: list[ExtractedChart]
    │   ├── shape_name: str
    │   ├── chart_type: str
    │   ├── title: str | None
    │   ├── categories: list[str]
    │   └── series: list[ExtractedSeries]
    │       ├── name: str
    │       └── values: list[float | None]
    ├── tables: list[ExtractedTable]
    │   ├── shape_name: str
    │   └── rows: list[list[str]]
    ├── images: list[ExtractedImage]
    │   └── shape_name: str
    ├── footnotes: list[str]
    ├── speaker_notes: str | None
    └── background_color: str | None
```

### 5.2 CritiqueReport Schema (`schema/critique.py`)

Returned by the LLM after a review prompt. Also used as input to edit mode.

```
CritiqueReport
├── version: str
├── overall_score: int              # 0–100
├── summary: str                    # 2–3 sentence executive summary of findings
├── per_slide_scores: list[SlideScore]
│   ├── slide_number: int
│   ├── score: int                  # 0–100
│   └── summary: str               # One-sentence summary of slide issues
├── violations: list[Violation]
│   ├── violation_id: str           # e.g. "V001"
│   ├── rule_section: str           # e.g. "3.1" (from best_practices.md)
│   ├── rule_name: str              # e.g. "Action titles"
│   ├── severity: Literal["critical", "major", "minor"]
│   ├── slide_number: int | None    # null for deck-level violations
│   ├── location: str               # e.g. "title", "chart", "body", "deck-level"
│   ├── current_value: str | None   # What was found (e.g. current title text)
│   ├── suggested_fix: str          # Specific, actionable correction
│   └── explanation: str           # Why this violates the rule
└── checklist_results: ChecklistResults
    ├── story_structure: ChecklistSection       # Section 8.1
    ├── executive_communication: ChecklistSection # Section 8.2
    ├── data_visualization: ChecklistSection    # Section 8.3
    ├── slide_design: ChecklistSection          # Section 8.4
    └── overall_quality: ChecklistSection       # Section 8.6

ChecklistSection
├── passed: list[str]               # Rule names that passed
├── failed: list[str]               # Rule names that failed
└── score: int                      # 0–100 for this section
```

### 5.3 DeckStructure Schema (`schema/deck_structure.py`)

Returned by the LLM after a generate or edit prompt. Input to Phase 2 builder.

```
DeckStructure
├── version: str
├── metadata: DeckBuildMetadata
│   ├── title: str
│   ├── font_family: str            # e.g. "Calibri", "Arial"
│   └── color_palette: ColorPalette
│       ├── primary: str            # hex
│       ├── secondary: str          # hex
│       ├── accent: str             # hex (the "muted + accent" highlight color)
│       ├── positive: str           # hex — for growth/positive values
│       ├── negative: str           # hex — for decline/negative values
│       └── neutral: str           # hex — for context/secondary data
└── slides: list[Slide]
    ├── slide_number: int
    ├── layout: Literal["title_slide", "exec_summary", "data_slide",
    │                    "section_divider", "blank", "appendix"]
    ├── action_title: str           # Complete sentence, max 15 words
    ├── subtitle: str | None
    ├── body: SlideBody | None
    │   └── bullets: list[Bullet]
    │       ├── text: str
    │       ├── level: int          # 0 = top-level, 1 = indented, 2 = double-indented
    │       └── bold: bool
    ├── chart: ChartSpec | None
    │   ├── type: str               # See chart type mapping in Section 4.1
    │   ├── title: str
    │   ├── x_axis: AxisSpec
    │   │   ├── label: str          # Descriptive name + units, e.g. "Revenue ($M)"
    │   │   └── categories: list[str]
    │   ├── y_axis: AxisSpec
    │   │   ├── label: str
    │   │   └── start_at_zero: bool # Always True for bar charts
    │   ├── series: list[SeriesSpec]
    │   │   ├── name: str
    │   │   ├── values: list[float | None]
    │   │   └── color: str          # hex color
    │   └── annotations: list[ChartAnnotation]
    │       ├── series_name: str
    │       ├── value_index: int    # 0-based index into the series values
    │       └── text: str
    ├── footnotes: list[str]
    ├── speaker_notes: str | None
    └── page_number: int

ContentInput (input to generate mode — user-supplied)
├── version: str
├── topic: str                      # e.g. "Q3 2025 Retail Banking Executive Update"
├── audience: Literal["c_suite", "evp", "svp", "board"]
├── deck_type: Literal["earnings", "strategy", "initiative", "board", "general"]
├── key_messages: list[str]         # 2–5 top-level points for the deck
├── slides: list[ContentSlide]
│   ├── title_hint: str             # What this slide should be about
│   ├── data: dict | None           # Raw metrics/KPIs for the LLM to use
│   └── notes: str | None          # Freeform context for the LLM
└── metadata: dict | None          # Optional: date, author, entity name, etc.
```

---

## 6. Prompt Templates

All three templates live in `src/execudeck/prompts/`. They are plain text files
with `{PLACEHOLDER}` tokens filled at runtime. Users may override them by
placing custom templates in the directory specified by `execudeck.toml`.

### 6.1 `review.txt` — Review Prompt Template

Structure of the prompt:

1. **Role assignment**: "You are an expert presentation analyst..."
2. **Best practices rules**: `{BEST_PRACTICES}` — full `best_practices.md` content
3. **Task instruction**: "Review the following PowerPoint deck serialized as
   JSON against every applicable rule in the best practices above."
4. **Input deck**: `{DECK_JSON}` — the `DeckExtraction` JSON
5. **Output schema instruction**: "You MUST return a JSON object that exactly
   matches this schema. Return ONLY valid JSON — no prose, no markdown code
   fences."
6. **Output schema**: `{CRITIQUE_SCHEMA}` — the `CritiqueReport` JSON Schema
   (generated from Pydantic via `model_json_schema()`)
7. **Output format reminders**:
   - Return raw JSON only
   - Do not truncate
   - Severity definitions: critical = automatic fail per best_practices.md §7;
     major = significant quality impact; minor = polish

### 6.2 `generate.txt` — Generate Prompt Template

Structure of the prompt:

1. **Role assignment**: "You are an expert executive presentation builder..."
2. **Best practices rules**: `{BEST_PRACTICES}`
3. **Task instruction**: "Build a complete executive presentation deck using
   the content input below. Every slide must comply with the best practices
   above."
4. **Input content**: `{CONTENT_JSON}` — the `ContentInput` JSON
5. **Output schema instruction** + `{DECK_STRUCTURE_SCHEMA}`
6. **Output format reminders**:
   - Return raw JSON only
   - All action titles must be complete sentences with a verb, max 15 words
   - All bar chart y-axes must have `start_at_zero: true`
   - Color palette must follow semantic coding (green = positive, red = negative)
   - Slide count must be 10–15 for most decks; never exceed 20 in main flow

### 6.3 `edit.txt` — Edit Prompt Template

Structure of the prompt:

1. **Role assignment**: "You are an expert executive presentation editor..."
2. **Best practices rules**: `{BEST_PRACTICES}`
3. **Task instruction**: "You are given an existing deck (as JSON) and a
   critique report identifying all violations. Produce a corrected version of
   the deck that fixes every violation in the critique."
4. **Existing deck**: `{DECK_JSON}` — the `DeckExtraction` JSON
5. **Critique report**: `{CRITIQUE_JSON}` — the `CritiqueReport` JSON
6. **Output schema instruction** + `{DECK_STRUCTURE_SCHEMA}`
7. **Output format reminders**: same as generate, plus:
   - Address every `critical` and `major` violation
   - Preserve slides and content not flagged in the critique
   - Do not add slides unless needed to fix a structural violation

---

## 7. CLI Design

Implemented with `click`. Entry point: `execudeck` (registered in `pyproject.toml`).

### Commands

#### `execudeck review <PPTX_PATH>`

Phase 1 for review mode.

```
execudeck review deck.pptx [--output-dir DIR] [--template PATH] [--config PATH]
```

- Reads `deck.pptx`
- Extracts full deck content → `<output_dir>/deck_extraction.json`
- Fills `review.txt` prompt template
- Saves prompt → `<output_dir>/review_prompt.txt`
- Prints to terminal:
  ```
  [execudeck] Deck extracted: output/deck_extraction.json
  [execudeck] Review prompt saved: output/review_prompt.txt

  NEXT STEPS:
  1. Open output/review_prompt.txt
  2. Copy the full contents and paste into your LLM (Copilot, Gemini, etc.)
  3. Save the LLM's JSON response to a file, e.g. output/critique.json
  4. Run: execudeck build output/critique.json
  ```

#### `execudeck generate <CONTENT_JSON_PATH>`

Phase 1 for generate mode.

```
execudeck generate content.json [--output-dir DIR] [--template PATH] [--config PATH]
```

- Validates `content.json` against `ContentInput` schema
- Fills `generate.txt` prompt template
- Saves prompt → `<output_dir>/generate_prompt.txt`
- Prints next-steps instructions

#### `execudeck edit <PPTX_PATH> <CRITIQUE_JSON_PATH>`

Phase 1 for edit mode.

```
execudeck edit deck.pptx critique.json [--output-dir DIR] [--template PATH] [--config PATH]
```

- Reads `deck.pptx` → extracts to `<output_dir>/deck_extraction.json`
- Validates `critique.json` against `CritiqueReport` schema
- Fills `edit.txt` prompt template
- Saves prompt → `<output_dir>/edit_prompt.txt`
- Prints next-steps instructions

#### `execudeck build <JSON_PATH>`

Phase 2 for both generate and edit modes. Detects schema type automatically.

```
execudeck build deck_structure.json [--output-dir DIR] [--template PATH] [--output-name NAME] [--config PATH]
```

- Validates `deck_structure.json` against `DeckStructure` schema
  - On failure: print each validation error with field path and message; exit 1
- Loads template `.pptx` (from config or `--template` flag)
- Builds `.pptx` slide by slide
- Saves → `<output_dir>/<output_name>.pptx` (default name: `execudeck_output.pptx`)
- Prints:
  ```
  [execudeck] Built 14 slides
  [execudeck] Output saved: output/execudeck_output.pptx
  ```

Note: `execudeck build` also accepts a `CritiqueReport` JSON, in which case
it saves a formatted Markdown review report instead of a `.pptx`:

```
[execudeck] Review report saved: output/review_report.md
```

The Markdown report structure:

```markdown
# execudeck Review Report — <deck title>
Overall Score: 72/100

## Summary
<critique.summary>

## Violations by Severity

### Critical
...

### Major
...

### Minor
...

## Per-Slide Scores
| Slide | Score | Summary |
|---|---|---|
...

## Checklist Results
...
```

### Global CLI Options

| Option | Default | Description |
|---|---|---|
| `--output-dir DIR` | `./output` | Directory to write all output files |
| `--template PATH` | config value | Path to template `.pptx` file |
| `--config PATH` | `./execudeck.toml` | Path to config file |
| `--verbose` | False | Enable debug logging |

---

## 8. Configuration

### `execudeck.toml` (project root)

```toml
[output]
directory = "./output"

[template]
path = ""                   # Path to .pptx template; leave empty for blank presentation

[prompts]
directory = ""              # Optional: path to custom prompt templates directory
                            # Leave empty to use package-bundled prompts

[logging]
level = "INFO"              # DEBUG | INFO | WARNING | ERROR
```

### `config.py` Module

- Loads `execudeck.toml` using `tomllib` (Python 3.11+) or `tomli` for older versions
- Exposes a `Config` dataclass with typed fields
- Merges CLI flags over config file values (CLI wins)
- If config file is absent, falls back to hardcoded defaults
- Raises a clear `ConfigError` for invalid values (e.g. template path that
  doesn't exist, invalid log level)

---

## 9. Python Library API

The package exposes a clean public API from `__init__.py` for programmatic use
(in addition to the CLI):

```python
from execudeck import extract, review, generate, edit, build
from execudeck.schema import DeckExtraction, CritiqueReport, DeckStructure, ContentInput

# Phase 1 — extract
deck: DeckExtraction = extract("deck.pptx")

# Phase 1 — generate prompt files
review_prompt_path = review("deck.pptx", output_dir="./output")
generate_prompt_path = generate("content.json", output_dir="./output")
edit_prompt_path = edit("deck.pptx", "critique.json", output_dir="./output")

# Phase 2 — build .pptx
output_path = build("deck_structure.json", output_dir="./output", template="template.pptx")

# Schema loading helpers
critique = CritiqueReport.model_validate_json(Path("critique.json").read_text())
structure = DeckStructure.model_validate_json(Path("deck_structure.json").read_text())
```

---

## 10. Dependencies & Package Metadata

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "execudeck"
version = "0.1.0"
description = "Review, generate, and edit executive PowerPoint presentations"
requires-python = ">=3.11"
dependencies = [
    "python-pptx>=0.6.23",
    "click>=8.1",
    "pydantic>=2.0",
    "tomli>=2.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
]

[project.scripts]
execudeck = "execudeck.cli:cli"
```

### Rationale for each dependency

| Package | Version | Purpose |
|---|---|---|
| `python-pptx` | ≥0.6.23 | Read and write `.pptx` files; add slides, shapes, charts |
| `click` | ≥8.1 | CLI framework with command groups, options, help text |
| `pydantic` | ≥2.0 | JSON schema validation with clear field-level errors; model serialization |
| `tomli` | ≥2.0 | TOML config parsing for Python < 3.11 (3.11+ uses built-in `tomllib`) |

---

## 11. Testing Plan

### Test fixtures (`tests/conftest.py`)

- `sample_pptx` — a minimal `.pptx` built programmatically with python-pptx:
  - 3 slides: title slide, data slide with a bar chart, and a text slide
  - Intentional violations: topic titles (not action titles), truncated axis
- `sample_critique_json` — a valid `CritiqueReport` JSON matching the schema
- `sample_deck_structure_json` — a valid `DeckStructure` JSON with 3 slides
  including one bar chart
- `sample_content_json` — a valid `ContentInput` JSON

### Test modules

#### `test_extractor.py`
- `test_extract_returns_deck_extraction_model` — result is a `DeckExtraction`
- `test_extract_title_captured` — title text from slide 1 matches fixture
- `test_extract_body_shapes_captured` — body paragraphs are present
- `test_extract_chart_captured` — chart shape is extracted with type and series
- `test_extract_footnotes_detected` — small-font bottom text identified as footnote
- `test_extract_speaker_notes` — notes pane text is captured
- `test_extract_invalid_path_raises` — `FileNotFoundError` on missing file

#### `test_builder.py`
- `test_build_creates_pptx_file` — output file exists after build
- `test_build_slide_count_matches_schema` — pptx slide count equals schema
- `test_build_action_title_set` — first slide title text matches schema
- `test_build_chart_inserted` — slide with chart spec has a chart shape
- `test_build_footnotes_present` — footnote text box present on slide with footnotes
- `test_build_bar_chart_zero_axis_enforced` — y-axis min is 0 for bar charts
- `test_build_invalid_json_exits_with_error` — invalid schema → exit code 1 + message

#### `test_reviewer.py`
- `test_review_creates_prompt_file` — `review_prompt.txt` written to output dir
- `test_review_creates_extraction_json` — `deck_extraction.json` written
- `test_review_prompt_contains_best_practices` — prompt includes best_practices.md text
- `test_review_prompt_contains_deck_json` — prompt includes serialized deck

#### `test_generator.py`
- `test_generate_creates_prompt_file` — `generate_prompt.txt` written
- `test_generate_validates_content_input` — invalid content JSON raises `ValidationError`

#### `test_editor.py`
- `test_edit_creates_prompt_file` — `edit_prompt.txt` written
- `test_edit_prompt_contains_critique` — prompt includes critique JSON

#### `test_schema_extraction.py`
- `test_deck_extraction_valid` — valid dict passes Pydantic validation
- `test_deck_extraction_missing_required_field` — raises `ValidationError`

#### `test_schema_critique.py`
- `test_critique_report_valid` — valid dict passes
- `test_critique_severity_enum` — only "critical"/"major"/"minor" accepted
- `test_critique_score_range` — score > 100 raises `ValidationError`

#### `test_schema_deck_structure.py`
- `test_deck_structure_valid` — valid dict passes
- `test_slide_layout_enum` — invalid layout string raises `ValidationError`
- `test_chart_type_accepted` — all supported chart type strings pass
- `test_action_title_required` — missing action title raises error

#### `test_config.py`
- `test_config_loads_toml` — config file is read and fields populated
- `test_config_cli_overrides_file` — CLI option takes precedence over file
- `test_config_missing_file_uses_defaults` — no config file → defaults applied
- `test_config_invalid_template_path_raises` — non-existent path → `ConfigError`

#### `test_cli.py`
- `test_review_command` — `CliRunner.invoke(review, ["deck.pptx"])` → exit code 0
- `test_generate_command` — `CliRunner.invoke(generate, ["content.json"])` → exit code 0
- `test_edit_command` — `CliRunner.invoke(edit, ["deck.pptx", "critique.json"])` → exit code 0
- `test_build_command` — `CliRunner.invoke(build, ["deck_structure.json"])` → exit code 0
- `test_build_invalid_json` — `CliRunner.invoke(build, ["bad.json"])` → exit code 1

---

## 12. Implementation Task Checklist

Tasks are ordered by dependency. Complete them in sequence within each phase.

### Phase A — Project Scaffolding

- [x] Create `src/execudeck/` directory structure
- [x] Create `src/execudeck/__init__.py` with public API stubs
- [x] Create `pyproject.toml` with all metadata, dependencies, and entry points
- [x] Create `execudeck.toml` default config at project root
- [x] Create `tests/` directory with empty `conftest.py`
- [x] Verify `pip install -e ".[dev]"` installs successfully
- [x] Verify `execudeck --help` prints CLI usage

### Phase B — Configuration

- [x] Implement `config.py`:
  - [x] `Config` dataclass with all fields (output_dir, template_path, prompts_dir, log_level)
  - [x] `load_config(path)` function using `tomllib` / `tomli`
  - [x] Default fallback values
  - [x] `ConfigError` exception class
  - [x] Validation of template path existence (warn if missing, don't error)
- [x] Write `test_config.py` tests; all passing

### Phase C — JSON Schemas (Pydantic Models)

- [x] Implement `schema/extraction.py`:
  - [x] `ExtractedParagraph`, `ExtractedShape`, `ExtractedChart`, `ExtractedSeries`
  - [x] `ExtractedTable`, `ExtractedImage`
  - [x] `ThemeFonts`, `DeckMetadata`
  - [x] `ExtractedSlide`
  - [x] `DeckExtraction` root model
- [x] Implement `schema/critique.py`:
  - [x] `Violation`, `SlideScore`, `ChecklistSection`, `ChecklistResults`
  - [x] `CritiqueReport` root model
- [x] Implement `schema/deck_structure.py`:
  - [x] `ColorPalette`, `DeckBuildMetadata`
  - [x] `Bullet`, `SlideBody`
  - [x] `AxisSpec`, `SeriesSpec`, `ChartAnnotation`, `ChartSpec`
  - [x] `Slide`
  - [x] `DeckStructure` root model
  - [x] `ContentSlide`, `ContentInput` (for generate mode input)
- [x] Implement `schema/__init__.py` re-exports
- [x] Write schema test files; all passing

### Phase D — Extractor

- [x] Implement `extractor.py`:
  - [x] `extract(pptx_path: str | Path) -> DeckExtraction`
  - [x] Slide iteration with shape type detection
  - [x] Text frame extraction with paragraph-level formatting
  - [x] Chart extraction (type, categories, series, title)
  - [x] Table extraction (row/cell text)
  - [x] Image detection (name only)
  - [x] Footnote heuristic (font size ≤ 12pt AND positioned in bottom 15%)
  - [x] Speaker notes extraction
  - [x] Deck metadata extraction (core properties, theme fonts/colors)
- [x] Write `test_extractor.py` tests; all passing

### Phase E — Prompt Templates

- [x] Write `src/execudeck/prompts/review.txt`:
  - [x] Role assignment block
  - [x] `{BEST_PRACTICES}` placeholder
  - [x] Task instruction block
  - [x] `{DECK_JSON}` placeholder
  - [x] Output schema instruction
  - [x] `{CRITIQUE_SCHEMA}` placeholder
  - [x] JSON-only output reminders
- [x] Write `src/execudeck/prompts/generate.txt`:
  - [x] Role assignment block
  - [x] `{BEST_PRACTICES}` placeholder
  - [x] Task instruction block
  - [x] `{CONTENT_JSON}` placeholder
  - [x] Slide count, action title, color semantics reminders
  - [x] `{DECK_STRUCTURE_SCHEMA}` placeholder
- [x] Write `src/execudeck/prompts/edit.txt`:
  - [x] Role assignment block
  - [x] `{BEST_PRACTICES}` placeholder
  - [x] Task instruction block
  - [x] `{DECK_JSON}` placeholder
  - [x] `{CRITIQUE_JSON}` placeholder
  - [x] Fix-all-critical-and-major instruction
  - [x] `{DECK_STRUCTURE_SCHEMA}` placeholder
- [x] Implement prompt-loading utility: `load_prompt(template_name, overrides_dir=None) -> str`
- [x] Implement prompt-filling utility: `fill_prompt(template: str, **kwargs) -> str`

### Phase F — Phase 1 Orchestrators

- [x] Implement `reviewer.py`:
  - [x] `review(pptx_path, output_dir, config) -> Path` (returns prompt path)
  - [x] Calls extractor, fills prompt, writes files, prints instructions
- [x] Implement `generator.py`:
  - [x] `generate(content_json_path, output_dir, config) -> Path`
  - [x] Validates ContentInput, fills prompt, writes file, prints instructions
- [x] Implement `editor.py`:
  - [x] `edit(pptx_path, critique_json_path, output_dir, config) -> Path`
  - [x] Calls extractor, validates CritiqueReport, fills prompt, writes files
- [x] Write `test_reviewer.py`, `test_generator.py`, `test_editor.py`; all passing

### Phase G — Builder

- [x] Implement `builder.py`:
  - [x] `build(json_path, output_dir, template_path, output_name, config) -> Path`
  - [x] JSON type detection (DeckStructure vs CritiqueReport)
  - [x] Pydantic validation with field-level error reporting
  - [x] Template loading (or blank presentation fallback)
  - [x] Slide layout mapping from layout name strings to template indices
  - [x] Per-slide construction loop:
    - [x] Title placeholder population
    - [x] Subtitle placeholder population
    - [x] Body bullet population with level and bold support
    - [x] Chart insertion with `ChartData` and `XL_CHART_TYPE` mapping
    - [x] Bar chart y-axis zero enforcement
    - [x] Series color application
    - [x] Legend removal + direct label placement
    - [x] Annotation text boxes
    - [x] Footnote text box (bottom of slide)
    - [x] Speaker notes population
    - [x] Page number insertion
  - [x] Deck-level consistency check (title position stability warning)
  - [x] Output `.pptx` save
  - [x] Markdown review report generation (for CritiqueReport input)
- [x] Write `test_builder.py` tests; all passing

### Phase H — CLI

- [x] Implement `cli.py`:
  - [x] `@click.group()` root command
  - [x] `review` subcommand with options
  - [x] `generate` subcommand with options
  - [x] `edit` subcommand with options
  - [x] `build` subcommand with options
  - [x] Config loading and CLI flag merge in each command
  - [x] `--verbose` → set log level to DEBUG
  - [x] Graceful error handling: catch `ValidationError`, `ConfigError`,
        `FileNotFoundError` → print friendly message → exit 1
- [x] Write `test_cli.py` tests; all passing

### Phase I — Public API & `__init__.py`

- [x] Expose `extract`, `review`, `generate`, `edit`, `build` functions
- [x] Expose schema models: `DeckExtraction`, `CritiqueReport`, `DeckStructure`, `ContentInput`
- [x] Add `__version__ = "0.1.0"`

### Phase J — Final Validation

- [x] Run full test suite: `pytest --cov=execudeck tests/`
- [x] Manual end-to-end test — review mode:
  - [x] Run `execudeck review` on a sample `.pptx`
  - [x] Verify `deck_extraction.json` and `review_prompt.txt` are written
  - [x] Verify prompt contains best_practices content and deck JSON
- [x] Manual end-to-end test — generate mode:
  - [x] Run `execudeck generate` on a sample `content.json`
  - [x] Verify `generate_prompt.txt` is written with correct placeholders filled
- [x] Manual end-to-end test — build mode:
  - [x] Run `execudeck build` on a hand-written `deck_structure.json`
  - [x] Verify output `.pptx` opens in PowerPoint/LibreOffice with correct slides
  - [x] Verify charts are inserted, titles set, footnotes present
- [x] Manual end-to-end test — build with CritiqueReport:
  - [x] Run `execudeck build` on a hand-written `critique.json`
  - [x] Verify Markdown report is written with scores and violations
- [x] Verify `pip install -e .` and `execudeck --help` work on a clean install
