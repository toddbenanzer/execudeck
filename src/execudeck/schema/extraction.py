"""
Extraction Schema Definitions.

Provides Pydantic models mapping to the extracted components of a PowerPoint
deck (e.g., ExtractedShape, ExtractedChart, DeckMetadata, ThemeFonts).
"""
from pydantic import BaseModel
from typing import List, Optional

class ExtractedParagraph(BaseModel):
    text: str
    level: int = 0
    bold: bool = False
    italic: bool = False

class ExtractedShape(BaseModel):
    shape_name: str
    shape_type: str
    paragraphs: List[ExtractedParagraph] = []

class ExtractedSeries(BaseModel):
    name: str
    values: List[float | None]

class ExtractedChart(BaseModel):
    shape_name: str
    chart_type: str
    title: Optional[str] = None
    categories: List[str]
    series: List[ExtractedSeries]

class ExtractedTable(BaseModel):
    shape_name: str
    rows: List[List[str]]

class ExtractedImage(BaseModel):
    shape_name: str
    image_name: str

class ExtractedSlide(BaseModel):
    slide_number: int
    layout_name: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    body_shapes: List[ExtractedShape] = []
    charts: List[ExtractedChart] = []
    tables: List[ExtractedTable] = []
    images: List[ExtractedImage] = []
    footnotes: List[str] = []
    speaker_notes: Optional[str] = None

class ThemeFonts(BaseModel):
    major_font: str
    minor_font: str

class DeckMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    theme_fonts: ThemeFonts

class DeckExtraction(BaseModel):
    metadata: DeckMetadata
    slides: List[ExtractedSlide]
