import pytest
import json
from click.testing import CliRunner
from execudeck.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def sample_files(tmp_path, create_sample_pptx):
    # Setup paths
    pptx_path = tmp_path / "sample.pptx"
    create_sample_pptx(str(pptx_path))

    content_json = tmp_path / "content.json"
    content_json.write_text(json.dumps({
        "objective": "Test",
        "audience": "Test",
        "content_slides": [{"key_message": "Message", "supporting_points": ["Point"]}]
    }))

    deck_json = tmp_path / "deck.json"
    deck_json.write_text(json.dumps({
        "metadata": {"title": "Test", "color_palette": {"primary": "#000", "secondary": "#FFF", "accent_1": "#111", "accent_2": "#222"}},
        "slides": [{"slide_number": 1, "layout": "Title Slide", "action_title": "Test"}]
    }))

    critique_json = tmp_path / "critique.json"
    critique_json.write_text(json.dumps({
        "overall_score": 90,
        "summary": "Good",
        "checklist": {
            "storyline": {"section_name": "S", "passed": True, "details": "d"},
            "formatting": {"section_name": "F", "passed": True, "details": "d"},
            "data_viz": {"section_name": "D", "passed": True, "details": "d"},
            "action_titles": {"section_name": "A", "passed": True, "details": "d"}
        },
        "slide_scores": []
    }))

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json")

    return {
        "pptx": str(pptx_path),
        "content": str(content_json),
        "deck": str(deck_json),
        "critique": str(critique_json),
        "bad": str(bad_json),
        "outdir": str(tmp_path / "out")
    }

def test_review_command(runner, sample_files):
    result = runner.invoke(cli, ["review", sample_files["pptx"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 0
    assert "Review complete" in result.output

def test_generate_command(runner, sample_files):
    result = runner.invoke(cli, ["generate", sample_files["content"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 0
    assert "Generate complete" in result.output

def test_edit_command(runner, sample_files):
    result = runner.invoke(cli, ["edit", sample_files["pptx"], sample_files["critique"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 0
    assert "Edit complete" in result.output

def test_build_command(runner, sample_files):
    result = runner.invoke(cli, ["build", sample_files["deck"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 0
    assert "Build complete" in result.output

def test_build_invalid_json(runner, sample_files):
    result = runner.invoke(cli, ["build", sample_files["bad"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 1
    assert "Error:" in result.output

def test_cli_verbose_flag(runner, sample_files):
    result = runner.invoke(cli, ["--verbose", "build", sample_files["deck"], "--output-dir", sample_files["outdir"]])
    assert result.exit_code == 0
