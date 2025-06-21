"""CLI module for European Soccer Analytics platform."""

import logging
import typer
from rich.console import Console
from rich.logging import RichHandler

from soccer_analytics.config.settings import settings

# Configure logging
console = Console()

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

# Create the main Typer app
app = typer.Typer(
    name="soccer-analytics",
    help="European Soccer Analytics Platform CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

# Import and register command modules
from .commands import (
    database_commands,
    data_commands,
    analytics_commands,
    dashboard_commands
)

app.add_typer(database_commands.app, name="db", help="Database management commands")
app.add_typer(data_commands.app, name="data", help="Data fetching and processing commands")
app.add_typer(analytics_commands.app, name="analytics", help="Analytics and metrics commands")
app.add_typer(dashboard_commands.app, name="dashboard", help="Dashboard management commands")