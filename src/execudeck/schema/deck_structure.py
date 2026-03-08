"""
Deck Structure Schema Definitions.

Provides Pydantic models mapping to the final Deck Build schema, which
structurally defines metadata, slide layouts, and component specs like
charts, text bodies, colors, and content slides.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class ColorPalette(BaseModel):
    primary: str
    secondary: str
    accent_1: str
    accent_2: str

class DeckBuildMetadata(BaseModel):
    title: str
    color_palette: ColorPalette

class Bullet(BaseModel):
    text: str
    level: int = 0
    bold: bool = False

class SlideBody(BaseModel):
    bullets: List[Bullet] = []

class AxisSpec(BaseModel):
    title: Optional[str] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None

class SeriesSpec(BaseModel):
    name: str
    values: List[float | None]
    color: Optional[str] = None

class ChartAnnotation(BaseModel):
    text: str
    target_series: Optional[str] = None
    target_category: Optional[str] = None

class ChartSpec(BaseModel):
    chart_type: Literal[
        "COLUMN_CLUSTERED",
        "COLUMN_STACKED",
        "COLUMN_STACKED_100",
        "BAR_CLUSTERED",
        "BAR_STACKED",
        "BAR_STACKED_100",
        "LINE",
        "PIE",
        "DOUGHNUT"
    ]
    title: Optional[str] = None
    categories: List[str]
    series: List[SeriesSpec]
    x_axis: Optional[AxisSpec] = None
    y_axis: Optional[AxisSpec] = None
    annotations: List[ChartAnnotation] = []

class Slide(BaseModel):
    slide_number: int
    layout: Literal[
        "Title Slide",
        "Title and Content",
        "Section Header",
        "Two Content",
        "Comparison",
        "Title Only",
        "Blank",
        "Content with Caption",
        "Picture with Caption"
    ]
    action_title: str
    subtitle: Optional[str] = None
    body: Optional[SlideBody] = None
    chart: Optional[ChartSpec] = None
    footnotes: List[str] = []
    speaker_notes: Optional[str] = None

class DeckStructure(BaseModel):
    metadata: DeckBuildMetadata
    slides: List[Slide]

class ContentSlide(BaseModel):
    key_message: str
    supporting_points: List[str]
    data_table: Optional[List[Dict[str, Any]]] = None

class ContentInput(BaseModel):
    objective: str
    audience: str
    content_slides: List[ContentSlide]
