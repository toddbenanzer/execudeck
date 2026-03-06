import click
import sys
import logging
from pathlib import Path
from pydantic import ValidationError
from functools import wraps

from .config import load_config, ConfigError
from .reviewer import review as run_review
from .generator import generate as run_generate
from .editor import edit as run_edit
from .builder import build as run_build

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def handle_errors(func):
    """Decorator to catch expected exceptions and exit gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValidationError, ConfigError, FileNotFoundError, ValueError) as e:
            click.secho(f"Error: {str(e)}", fg="red", err=True)
            sys.exit(1)
        except Exception as e:
            click.secho(f"Unexpected error: {str(e)}", fg="red", err=True)
            sys.exit(1)
    return wrapper

@click.group()
@click.option('--config', type=click.Path(exists=False), help='Path to configuration file.')
@click.option('--verbose', is_flag=True, help='Enable verbose output (DEBUG level).')
@click.pass_context
def cli(ctx, config, verbose):
    """execudeck: Review, generate, and edit executive PowerPoint presentations."""
    setup_logging(verbose)

    try:
        cfg = load_config(config)
        if verbose:
            cfg.log_level = "DEBUG"
        ctx.obj = cfg
    except ConfigError as e:
        click.secho(f"Configuration error: {e}", fg="red", err=True)
        sys.exit(1)

@cli.command()
@click.argument('pptx_path', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Directory to write outputs.')
@click.pass_obj
@handle_errors
def review(config, pptx_path, output_dir):
    """Review mode: Extract deck content and generate a review prompt."""
    if output_dir:
        config.output_dir = output_dir
    prompt_path = run_review(pptx_path, config.output_dir, config)
    click.secho(f"Review complete. Prompt written to: {prompt_path}", fg="green")

@cli.command()
@click.argument('content_json', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Directory to write outputs.')
@click.pass_obj
@handle_errors
def generate(config, content_json, output_dir):
    """Generate mode: Convert structured content into a deck generation prompt."""
    if output_dir:
        config.output_dir = output_dir
    prompt_path = run_generate(content_json, config.output_dir, config)
    click.secho(f"Generate complete. Prompt written to: {prompt_path}", fg="green")

@cli.command()
@click.argument('pptx_path', type=click.Path(exists=True))
@click.argument('critique_json', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Directory to write outputs.')
@click.pass_obj
@handle_errors
def edit(config, pptx_path, critique_json, output_dir):
    """Edit mode: Combine an existing deck with a critique to generate an edit prompt."""
    if output_dir:
        config.output_dir = output_dir
    prompt_path = run_edit(pptx_path, critique_json, config.output_dir, config)
    click.secho(f"Edit complete. Prompt written to: {prompt_path}", fg="green")

@cli.command()
@click.argument('json_path', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), help='Directory to write outputs.')
@click.option('--template', type=click.Path(exists=True), help='PPTX template path.')
@click.option('--output-name', default="deck.pptx", help='Name of the output file.')
@click.pass_obj
@handle_errors
def build(config, json_path, output_dir, template, output_name):
    """Build mode: Generate a PPTX or Markdown report from JSON structure."""
    if output_dir:
        config.output_dir = output_dir
    tmpl = template or config.template_path

    out_path = run_build(json_path, config.output_dir, tmpl, output_name, config)
    click.secho(f"Build complete. Output written to: {out_path}", fg="green")

if __name__ == "__main__":
    cli()
