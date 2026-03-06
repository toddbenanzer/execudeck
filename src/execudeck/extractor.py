import os
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Pt
from execudeck.schema import (
    DeckExtraction, DeckMetadata, ThemeFonts, ExtractedSlide, ExtractedShape,
    ExtractedParagraph, ExtractedChart, ExtractedSeries, ExtractedTable, ExtractedImage
)

def _is_footnote(shape, slide_height):
    """
    Footnote heuristic: font size <= 12pt AND positioned in bottom 15% of the slide.
    """
    if not shape.has_text_frame:
        return False

    try:
        if shape.top is None or shape.height is None or slide_height is None:
            return False

        # Check position: bottom 15%
        bottom_edge = shape.top + shape.height
        if bottom_edge < slide_height * 0.85:
            return False

        # Check font size
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                if run.font.size and run.font.size > Pt(12):
                    return False
        return True
    except Exception:
        return False

def extract(pptx_path: str | Path) -> DeckExtraction:
    """Extract full content and metadata from a PowerPoint presentation."""
    path = Path(pptx_path)
    if not path.exists():
        raise FileNotFoundError(f"Presentation not found: {path}")

    prs = Presentation(str(path))
    slide_height = prs.slide_height

    # Basic deck metadata
    title = prs.core_properties.title if hasattr(prs.core_properties, 'title') else None
    author = prs.core_properties.author if hasattr(prs.core_properties, 'author') else None

    # Theme fonts extraction (heuristic or default as python-pptx support is limited)
    theme_fonts = ThemeFonts(major_font="Arial", minor_font="Arial")

    metadata = DeckMetadata(title=title, author=author, theme_fonts=theme_fonts)
    slides_data = []

    for idx, slide in enumerate(prs.slides, start=1):
        layout_name = slide.slide_layout.name if slide.slide_layout else "Blank"

        title_text = None
        subtitle_text = None

        if slide.shapes.title:
            title_text = slide.shapes.title.text

        # Very simple subtitle heuristic (often the second placeholder)
        placeholders = [s for s in slide.shapes if s.is_placeholder]
        if len(placeholders) > 1:
            try:
                 subtitle_text = placeholders[1].text if placeholders[1] != slide.shapes.title else None
            except Exception:
                 pass

        body_shapes = []
        charts = []
        tables = []
        images = []
        footnotes = []

        for shape in slide.shapes:
            # Check for footnote first
            if _is_footnote(shape, slide_height):
                footnotes.append(shape.text)
                continue

            shape_type_name = "UNKNOWN"
            try:
                shape_type_name = shape.shape_type.name if hasattr(shape, 'shape_type') else "UNKNOWN"
            except Exception:
                pass

            # Text Box / Placeholders
            if shape.has_text_frame and shape != slide.shapes.title and not (len(placeholders) > 1 and shape == placeholders[1]):
                paragraphs = []
                for p in shape.text_frame.paragraphs:
                    if not p.text.strip():
                        continue

                    # Calculate simple formatting based on the first run
                    is_bold = False
                    is_italic = False
                    if p.runs:
                        is_bold = bool(p.runs[0].font.bold)
                        is_italic = bool(p.runs[0].font.italic)

                    paragraphs.append(ExtractedParagraph(
                        text=p.text,
                        level=p.level,
                        bold=is_bold,
                        italic=is_italic
                    ))

                if paragraphs:
                    body_shapes.append(ExtractedShape(
                        shape_name=shape.name,
                        shape_type=shape_type_name,
                        paragraphs=paragraphs
                    ))

            # Tables
            elif shape.has_table:
                rows = []
                for row in shape.table.rows:
                    rows.append([cell.text_frame.text for cell in row.cells])
                tables.append(ExtractedTable(
                    shape_name=shape.name,
                    rows=rows
                ))

            # Charts
            elif shape.has_chart:
                chart = shape.chart
                # python-pptx chart type name
                chart_type_str = str(chart.chart_type).replace("XL_CHART_TYPE.", "")

                chart_title = chart.chart_title.text_frame.text if chart.has_title else None

                # Try to extract categories and series data
                categories = []
                series_data = []

                try:
                    categories = [str(c.label) for c in chart.plots[0].categories]
                    for s in chart.series:
                        values = [v for v in s.values]
                        series_data.append(ExtractedSeries(name=s.name, values=values))
                except Exception:
                    # In case of missing plots or unsupported chart types
                    pass

                charts.append(ExtractedChart(
                    shape_name=shape.name,
                    chart_type=chart_type_str,
                    title=chart_title,
                    categories=categories,
                    series=series_data
                ))

            # Images/Pictures
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                images.append(ExtractedImage(
                    shape_name=shape.name,
                    image_name=shape.name
                ))

        speaker_notes = None
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
             notes_text = slide.notes_slide.notes_text_frame.text
             if notes_text.strip():
                 speaker_notes = notes_text

        slides_data.append(ExtractedSlide(
            slide_number=idx,
            layout_name=layout_name,
            title=title_text,
            subtitle=subtitle_text,
            body_shapes=body_shapes,
            charts=charts,
            tables=tables,
            images=images,
            footnotes=footnotes,
            speaker_notes=speaker_notes
        ))

    return DeckExtraction(metadata=metadata, slides=slides_data)
