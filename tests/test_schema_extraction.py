import pytest
from pydantic import ValidationError
from execudeck.schema import DeckExtraction

def test_deck_extraction_valid():
    valid_data = {
        "metadata": {
            "title": "Test Deck",
            "author": "Author Name",
            "theme_fonts": {
                "major_font": "Arial",
                "minor_font": "Calibri"
            }
        },
        "slides": [
            {
                "slide_number": 1,
                "layout_name": "Title Slide",
                "title": "Main Title",
                "subtitle": "Subtitle",
                "body_shapes": [
                    {
                        "shape_name": "TextBox 1",
                        "shape_type": "TEXT_BOX",
                        "paragraphs": [
                            {"text": "Paragraph 1", "level": 0, "bold": True, "italic": False}
                        ]
                    }
                ],
                "charts": [
                    {
                        "shape_name": "Chart 1",
                        "chart_type": "COLUMN_CLUSTERED",
                        "title": "Test Chart",
                        "categories": ["A", "B"],
                        "series": [
                            {"name": "Series 1", "values": [1.0, 2.0]}
                        ]
                    }
                ],
                "tables": [
                    {
                        "shape_name": "Table 1",
                        "rows": [["Col1", "Col2"], ["Val1", "Val2"]]
                    }
                ],
                "images": [
                    {
                        "shape_name": "Image 1",
                        "image_name": "logo.png"
                    }
                ],
                "footnotes": ["Source: Test"],
                "speaker_notes": "Note"
            }
        ]
    }
    deck = DeckExtraction(**valid_data)
    assert deck.metadata.title == "Test Deck"
    assert deck.slides[0].slide_number == 1
    assert deck.slides[0].charts[0].chart_type == "COLUMN_CLUSTERED"

def test_deck_extraction_missing_required_field():
    invalid_data = {
        "metadata": {
            # missing theme_fonts which is required
            "title": "Test Deck"
        },
        "slides": []
    }
    with pytest.raises(ValidationError):
        DeckExtraction(**invalid_data)
