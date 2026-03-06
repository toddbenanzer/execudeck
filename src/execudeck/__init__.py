"""
execudeck: A package for reviewing, generating, and editing executive PowerPoint presentations.
"""

__version__ = "0.1.0"

from .extractor import extract
from .reviewer import review
from .generator import generate
from .editor import edit
from .builder import build
from .schema import DeckExtraction, CritiqueReport, DeckStructure, ContentInput

__all__ = [
    "extract",
    "review",
    "generate",
    "edit",
    "build",
    "DeckExtraction",
    "CritiqueReport",
    "DeckStructure",
    "ContentInput"
]
