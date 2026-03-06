import pytest
import tempfile
from pathlib import Path
from pptx import Presentation
from execudeck.extractor import extract

def test_extract_invalid_path_raises():
    with pytest.raises(FileNotFoundError):
        extract("nonexistent_path.pptx")

def test_extract_valid_pptx(tmp_path, create_sample_pptx):
    pptx_file = tmp_path / "sample.pptx"
    create_sample_pptx(pptx_file)

    deck = extract(pptx_file)

    # Basic Deck Validation
    assert deck.metadata is not None
    assert len(deck.slides) == 2

    # Slide 1 (Title layout)
    slide1 = deck.slides[0]
    assert slide1.slide_number == 1
    assert slide1.title == "Hello, World!"
    # Ensure subtitle extraction is somewhat accurate
    assert slide1.subtitle == "Subtitle here" or slide1.subtitle is None
    assert slide1.speaker_notes == "These are speaker notes."

    # Slide 2 (Blank layout)
    slide2 = deck.slides[1]
    assert slide2.slide_number == 2
    assert slide2.title is None
    # We expect 1 text box shape to be extracted from slide 2
    assert len(slide2.body_shapes) == 1
    assert slide2.body_shapes[0].paragraphs[0].text == "This is a text box"
