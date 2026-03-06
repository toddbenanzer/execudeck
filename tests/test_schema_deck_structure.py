import pytest
from pydantic import ValidationError
from execudeck.schema import DeckStructure, ContentInput

def test_deck_structure_valid():
    valid_data = {
        "metadata": {
            "title": "Strategy Deck",
            "color_palette": {
                "primary": "#000000",
                "secondary": "#FFFFFF",
                "accent_1": "#FF0000",
                "accent_2": "#00FF00"
            }
        },
        "slides": [
            {
                "slide_number": 1,
                "layout": "Title Slide",
                "action_title": "Project Alpha Launch",
                "subtitle": "Q3 2024 Readiness",
                "body": {
                    "bullets": [
                        {"text": "Key point 1", "level": 0, "bold": True},
                        {"text": "Sub-point 1a", "level": 1, "bold": False}
                    ]
                },
                "chart": {
                    "chart_type": "COLUMN_CLUSTERED",
                    "title": "Revenue Growth",
                    "categories": ["Q1", "Q2", "Q3", "Q4"],
                    "series": [
                        {"name": "Actual", "values": [10.5, 12.0, 15.0, None], "color": "#0000FF"},
                        {"name": "Forecast", "values": [None, None, 15.0, 18.0], "color": "#FF0000"}
                    ],
                    "x_axis": {"title": "Quarter"},
                    "y_axis": {"title": "Revenue ($M)", "min_val": 0, "max_val": 20},
                    "annotations": [
                        {"text": "Q3 Target Achieved", "target_series": "Forecast", "target_category": "Q3"}
                    ]
                },
                "footnotes": ["Source: Internal Data"],
                "speaker_notes": "Emphasize Q3 growth."
            }
        ]
    }
    deck = DeckStructure(**valid_data)
    assert deck.metadata.title == "Strategy Deck"
    assert len(deck.slides) == 1
    assert deck.slides[0].chart.chart_type == "COLUMN_CLUSTERED"
    assert deck.slides[0].chart.series[0].values[0] == 10.5

def test_slide_layout_enum():
    invalid_data = {
        "metadata": {
            "title": "Strategy Deck",
            "color_palette": {
                "primary": "#000000",
                "secondary": "#FFFFFF",
                "accent_1": "#FF0000",
                "accent_2": "#00FF00"
            }
        },
        "slides": [
            {
                "slide_number": 1,
                "layout": "Invalid Layout String",
                "action_title": "Project Alpha Launch",
                "subtitle": "Q3 2024 Readiness"
            }
        ]
    }
    with pytest.raises(ValidationError):
        DeckStructure(**invalid_data)

def test_chart_type_accepted():
    valid_data = {
        "metadata": {
            "title": "Strategy Deck",
            "color_palette": {
                "primary": "#000000",
                "secondary": "#FFFFFF",
                "accent_1": "#FF0000",
                "accent_2": "#00FF00"
            }
        },
        "slides": [
            {
                "slide_number": 1,
                "layout": "Title Slide",
                "action_title": "Project Alpha Launch",
                "chart": {
                    "chart_type": "PIE",  # valid chart type
                    "categories": ["A", "B"],
                    "series": [
                        {"name": "Series 1", "values": [1.0, 2.0]}
                    ]
                }
            }
        ]
    }
    deck = DeckStructure(**valid_data)
    assert deck.slides[0].chart.chart_type == "PIE"

def test_action_title_required():
    invalid_data = {
        "metadata": {
            "title": "Strategy Deck",
            "color_palette": {
                "primary": "#000000",
                "secondary": "#FFFFFF",
                "accent_1": "#FF0000",
                "accent_2": "#00FF00"
            }
        },
        "slides": [
            {
                "slide_number": 1,
                "layout": "Title Slide",
                # missing action_title
                "subtitle": "Q3 2024 Readiness"
            }
        ]
    }
    with pytest.raises(ValidationError):
        DeckStructure(**invalid_data)

def test_content_input_valid():
    valid_data = {
        "objective": "Present Q3 results",
        "audience": "Board of Directors",
        "content_slides": [
            {
                "key_message": "Strong revenue growth in Q3",
                "supporting_points": ["Revenue up 20%", "EBITDA up 15%"],
                "data_table": [{"Q1": 10, "Q2": 12, "Q3": 15}]
            }
        ]
    }
    content = ContentInput(**valid_data)
    assert content.objective == "Present Q3 results"
    assert content.content_slides[0].key_message == "Strong revenue growth in Q3"
