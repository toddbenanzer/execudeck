"""
Critique Schema Definitions.

Provides Pydantic models for the Critique Report, including slide scores,
rule violations, and checklist validations.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Violation(BaseModel):
    severity: Literal["critical", "major", "minor"]
    description: str
    suggested_fix: str

class SlideScore(BaseModel):
    slide_number: int
    score: int = Field(ge=0, le=100)
    violations: List[Violation] = []

class ChecklistSection(BaseModel):
    section_name: str
    passed: bool
    details: str

class ChecklistResults(BaseModel):
    storyline: ChecklistSection
    formatting: ChecklistSection
    data_viz: ChecklistSection
    action_titles: ChecklistSection

class CritiqueReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    summary: str
    checklist: ChecklistResults
    slide_scores: List[SlideScore]
