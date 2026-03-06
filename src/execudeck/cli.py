import click

@click.group()
def cli():
    """execudeck CLI tool."""
    pass

@cli.command()
def review():
    """Review mode."""
    pass

@cli.command()
def generate():
    """Generate mode."""
    pass

@cli.command()
def edit():
    """Edit mode."""
    pass

@cli.command()
def build():
    """Build mode."""
    pass

if __name__ == "__main__":
    cli()
