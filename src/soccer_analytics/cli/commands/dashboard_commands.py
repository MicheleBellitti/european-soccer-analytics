"""Dashboard management CLI commands."""

import subprocess
import sys
import threading
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from soccer_analytics.config.settings import settings

console = Console()
app = typer.Typer()


@app.command("start")
def start_dashboard(
    port: int = typer.Option(
        None,
        "--port",
        "-p",
        help=f"Port to run dashboard on (default: {settings.streamlit_port})"
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        help="Run in development mode with auto-reload"
    ),
    open_browser: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open browser automatically"
    )
):
    """Start the Streamlit dashboard."""
    try:
        # Determine port
        dashboard_port = port or settings.streamlit_port
        
        # Get the dashboard app path
        dashboard_path = Path(__file__).parent.parent.parent / "dashboard" / "app.py"
        
        if not dashboard_path.exists():
            console.print(f"[red]Dashboard app not found at {dashboard_path}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[bold blue]Starting Streamlit dashboard on port {dashboard_port}...[/bold blue]")
        
        # Build streamlit command
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", str(dashboard_port),
            "--server.address", "localhost"
        ]
        
        if not open_browser:
            cmd.extend(["--server.headless", "true"])
        
        if dev:
            cmd.extend(["--server.runOnSave", "true"])
        
        # Display startup info
        startup_panel = Panel(
            f"""[bold green]🚀 Starting European Soccer Analytics Dashboard[/bold green]

[cyan]Dashboard URL:[/cyan] http://localhost:{dashboard_port}
[cyan]Mode:[/cyan] {'Development' if dev else 'Production'}
[cyan]Auto-open browser:[/cyan] {'Yes' if open_browser else 'No'}

[yellow]Press Ctrl+C to stop the dashboard[/yellow]""",
            title="Dashboard Startup",
            border_style="green"
        )
        console.print(startup_panel)
        
        # Start the dashboard
        result = subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start dashboard: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting dashboard: {e}[/red]")
        raise typer.Exit(1)


@app.command("check")
def check_dashboard():
    """Check if dashboard dependencies are installed and working."""
    try:
        console.print("[bold blue]Checking dashboard dependencies...[/bold blue]")
        
        # Check if streamlit is installed
        try:
            import streamlit
            console.print(f"[green]✓ Streamlit installed (version {streamlit.__version__})[/green]")
        except ImportError:
            console.print("[red]✗ Streamlit not installed[/red]")
            return
        
        # Check if plotly is installed
        try:
            import plotly
            console.print(f"[green]✓ Plotly installed (version {plotly.__version__})[/green]")
        except ImportError:
            console.print("[red]✗ Plotly not installed[/red]")
            return
        
        # Check if pandas is installed
        try:
            import pandas
            console.print(f"[green]✓ Pandas installed (version {pandas.__version__})[/green]")
        except ImportError:
            console.print("[red]✗ Pandas not installed[/red]")
            return
        
        # Check if dashboard files exist
        dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
        app_path = dashboard_path / "app.py"
        
        if dashboard_path.exists():
            console.print(f"[green]✓ Dashboard directory found[/green]")
        else:
            console.print(f"[red]✗ Dashboard directory not found at {dashboard_path}[/red]")
            return
        
        if app_path.exists():
            console.print(f"[green]✓ Dashboard app found[/green]")
        else:
            console.print(f"[red]✗ Dashboard app not found at {app_path}[/red]")
            return
        
        # Check database connection
        from soccer_analytics.config.database import check_db_connection
        if check_db_connection():
            console.print("[green]✓ Database connection working[/green]")
        else:
            console.print("[red]✗ Database connection failed[/red]")
            return
        
        console.print("\n[bold green]✓ All dashboard checks passed![/bold green]")
        console.print("[cyan]You can start the dashboard with: soccer-analytics dashboard start[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error checking dashboard: {e}[/red]")
        raise typer.Exit(1)


@app.command("build")
def build_dashboard():
    """Build/prepare the dashboard for deployment."""
    try:
        console.print("[bold blue]Building dashboard for deployment...[/bold blue]")
        
        # Check if all required components are present
        dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
        required_files = [
            "app.py",
            "utils.py",
            "pages/01_League_Overview.py",
            "pages/02_Team_Analysis.py", 
            "pages/03_Player_Search.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (dashboard_path / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            console.print(f"[red]Missing dashboard files: {', '.join(missing_files)}[/red]")
            raise typer.Exit(1)
        
        # Run basic syntax check on dashboard files
        for file_path in required_files:
            if file_path.endswith('.py'):
                full_path = dashboard_path / file_path
                try:
                    with open(full_path, 'r') as f:
                        compile(f.read(), str(full_path), 'exec')
                    console.print(f"[green]✓ {file_path} syntax OK[/green]")
                except SyntaxError as e:
                    console.print(f"[red]✗ Syntax error in {file_path}: {e}[/red]")
                    raise typer.Exit(1)
        
        console.print("[bold green]✓ Dashboard build completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error building dashboard: {e}[/red]")
        raise typer.Exit(1)


@app.command("test")
def test_dashboard():
    """Run basic tests on dashboard components."""
    try:
        console.print("[bold blue]Testing dashboard components...[/bold blue]")
        
        # Test database connection
        from soccer_analytics.config.database import check_db_connection
        if check_db_connection():
            console.print("[green]✓ Database connection test passed[/green]")
        else:
            console.print("[red]✗ Database connection test failed[/red]")
            raise typer.Exit(1)
        
        # Test if we can import dashboard modules
        try:
            from soccer_analytics.dashboard import utils
            console.print("[green]✓ Dashboard utils import test passed[/green]")
        except ImportError as e:
            console.print(f"[red]✗ Dashboard utils import failed: {e}[/red]")
            raise typer.Exit(1)
        
        # Test analytics imports
        try:
            from soccer_analytics.analytics.metrics import AnalyticsEngine
            console.print("[green]✓ Analytics engine import test passed[/green]")
        except ImportError as e:
            console.print(f"[red]✗ Analytics engine import failed: {e}[/red]")
            raise typer.Exit(1)
        
        # Test basic data queries
        try:
            from soccer_analytics.config.database import get_db_session
            from soccer_analytics.data_models.models import League
            
            with get_db_session() as session:
                league_count = session.query(League).count()
                console.print(f"[green]✓ Basic data query test passed ({league_count} leagues found)[/green]")
        except Exception as e:
            console.print(f"[red]✗ Basic data query test failed: {e}[/red]")
            raise typer.Exit(1)
        
        console.print("[bold green]✓ All dashboard tests passed![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error testing dashboard: {e}[/red]")
        raise typer.Exit(1)


@app.command("config")
def show_dashboard_config():
    """Show current dashboard configuration."""
    try:
        console.print("[bold blue]Dashboard Configuration[/bold blue]")
        
        # Create configuration table
        from rich.table import Table
        config_table = Table(title="Current Settings")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="magenta")
        
        config_data = [
            ("Dashboard Port", str(settings.streamlit_port)),
            ("Debug Mode", str(settings.debug)),
            ("Database URL", settings.database_url.replace(settings.postgres_password, "***")),
            ("API Base URL", settings.football_data_base_url),
            ("Log Level", settings.log_level),
        ]
        
        for setting, value in config_data:
            config_table.add_row(setting, value)
        
        console.print(config_table)
        
        # Show dashboard paths
        dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
        
        path_panel = Panel(
            f"""[bold]Dashboard Paths:[/bold]

[cyan]Dashboard Directory:[/cyan] {dashboard_path}
[cyan]Main App:[/cyan] {dashboard_path / 'app.py'}
[cyan]Utils:[/cyan] {dashboard_path / 'utils.py'}
[cyan]Pages Directory:[/cyan] {dashboard_path / 'pages'}""",
            title="File Locations",
            border_style="blue"
        )
        console.print(path_panel)
        
    except Exception as e:
        console.print(f"[red]Error showing dashboard config: {e}[/red]")
        raise typer.Exit(1)