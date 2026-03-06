import pytest
from pydantic import ValidationError
from execudeck.schema import CritiqueReport

def test_critique_report_valid():
    valid_data = {
        "overall_score": 85,
        "summary": "Good deck, needs minor tweaks.",
        "checklist": {
            "storyline": {"section_name": "Storyline", "passed": True, "details": "Clear flow."},
            "formatting": {"section_name": "Formatting", "passed": False, "details": "Inconsistent fonts."},
            "data_viz": {"section_name": "Data Viz", "passed": True, "details": "Good charts."},
            "action_titles": {"section_name": "Action Titles", "passed": True, "details": "Strong titles."}
        },
        "slide_scores": [
            {
                "slide_number": 1,
                "score": 90,
                "violations": []
            },
            {
                "slide_number": 2,
                "score": 60,
                "violations": [
                    {
                        "severity": "major",
                        "description": "Chart is too small.",
                        "suggested_fix": "Increase chart size."
                    }
                ]
            }
        ]
    }
    report = CritiqueReport(**valid_data)
    assert report.overall_score == 85
    assert len(report.slide_scores) == 2
    assert report.slide_scores[1].violations[0].severity == "major"

def test_critique_severity_enum():
    invalid_data = {
        "overall_score": 85,
        "summary": "Good deck, needs minor tweaks.",
        "checklist": {
            "storyline": {"section_name": "Storyline", "passed": True, "details": "Clear flow."},
            "formatting": {"section_name": "Formatting", "passed": False, "details": "Inconsistent fonts."},
            "data_viz": {"section_name": "Data Viz", "passed": True, "details": "Good charts."},
            "action_titles": {"section_name": "Action Titles", "passed": True, "details": "Strong titles."}
        },
        "slide_scores": [
            {
                "slide_number": 2,
                "score": 60,
                "violations": [
                    {
                        "severity": "invalid_severity",  # Must be 'critical', 'major', 'minor'
                        "description": "Bad.",
                        "suggested_fix": "Fix."
                    }
                ]
            }
        ]
    }
    with pytest.raises(ValidationError):
        CritiqueReport(**invalid_data)

def test_critique_score_range():
    invalid_data = {
        "overall_score": 105,  # Valid range is 0-100
        "summary": "Good deck, needs minor tweaks.",
        "checklist": {
            "storyline": {"section_name": "Storyline", "passed": True, "details": "Clear flow."},
            "formatting": {"section_name": "Formatting", "passed": False, "details": "Inconsistent fonts."},
            "data_viz": {"section_name": "Data Viz", "passed": True, "details": "Good charts."},
            "action_titles": {"section_name": "Action Titles", "passed": True, "details": "Strong titles."}
        },
        "slide_scores": []
    }
    with pytest.raises(ValidationError):
        CritiqueReport(**invalid_data)
