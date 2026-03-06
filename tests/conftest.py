import pytest
from pptx import Presentation

@pytest.fixture
def create_sample_pptx():
    def _create(path):
        prs = Presentation()

        # Title slide
        title_slide_layout = prs.slide_layouts[0]
        slide1 = prs.slides.add_slide(title_slide_layout)
        title1 = slide1.shapes.title
        subtitle1 = slide1.placeholders[1]
        title1.text = "Hello, World!"
        subtitle1.text = "Subtitle here"

        # Notes on slide 1
        notes_slide = slide1.notes_slide
        notes_slide.notes_text_frame.text = "These are speaker notes."

        # Blank slide with a text box
        blank_slide_layout = prs.slide_layouts[6]
        slide2 = prs.slides.add_slide(blank_slide_layout)
        txBox = slide2.shapes.add_textbox(left=0, top=0, width=100, height=100)
        tf = txBox.text_frame
        tf.text = "This is a text box"

        prs.save(path)
        return path
    return _create
