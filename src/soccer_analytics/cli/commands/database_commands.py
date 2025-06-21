"""Database management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from soccer_analytics.config.database import init_db, drop_db, check_db_connection

console = Console()
app = typer.Typer()


@app.command("init")
def init_database():
    """Initialize the database schema."""
    try:
        console.print("[bold blue]Initializing database...[/bold blue]")
        
        if not check_db_connection():
            console.print("[bold red]✗ Database connection failed[/bold red]")
            console.print("[yellow]Please check your database configuration[/yellow]")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating database tables...", total=None)
            init_db()
            
        console.print("[bold green]✓ Database initialized successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error initializing database: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("check")
def check_database():
    """Check database connection and status."""
    try:
        console.print("[bold blue]Checking database connection...[/bold blue]")
        
        if check_db_connection():
            console.print("[bold green]✓ Database connection successful![/bold green]")
            
            # Show table information
            from soccer_analytics.config.database import get_db_session
            from soccer_analytics.data_models.models import League, Team, Player, Match, PlayerStats, TeamStats
            
            with get_db_session() as session:
                table = Table(title="Database Tables Status")
                table.add_column("Table", style="cyan")
                table.add_column("Record Count", style="magenta")
                table.add_column("Status", style="green")
                
                tables_info = [
                    ("leagues", League),
                    ("teams", Team),
                    ("players", Player),
                    ("matches", Match),
                    ("player_stats", PlayerStats),
                    ("team_stats", TeamStats)
                ]
                
                for table_name, model_class in tables_info:
                    try:
                        count = session.query(model_class).count()
                        status = "✓ OK" if count > 0 else "Empty"
                        table.add_row(table_name, str(count), status)
                    except Exception as e:
                        table.add_row(table_name, "Error", f"✗ {str(e)[:30]}...")
                
                console.print(table)
                
        else:
            console.print("[bold red]✗ Database connection failed![/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]✗ Error checking database: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("reset")
def reset_database(
    confirm: bool = typer.Option(
        False,
        "--confirm",
        "-y",
        help="Confirm the reset operation"
    )
):
    """Reset the database (DROP and recreate all tables)."""
    if not confirm:
        console.print("[bold yellow]⚠️  WARNING: This will delete ALL data in the database![/bold yellow]")
        confirm_input = typer.confirm("Are you sure you want to continue?")
        if not confirm_input:
            console.print("[cyan]Operation cancelled[/cyan]")
            return
    
    try:
        console.print("[bold blue]Resetting database...[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Dropping existing tables...", total=None)
            drop_db()
            
            progress.update(task, description="Creating new tables...")
            init_db()
        
        console.print("[bold green]✓ Database reset completed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error resetting database: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("vacuum")
def vacuum_database():
    """Optimize the database (PostgreSQL VACUUM operation)."""
    try:
        console.print("[bold blue]Optimizing database...[/bold blue]")
        
        from soccer_analytics.config.database import get_db_session
        
        with get_db_session() as session:
            # Check if it's PostgreSQL
            if "postgresql" in str(session.bind.url):
                console.print("[cyan]Running VACUUM on PostgreSQL database...[/cyan]")
                session.execute("VACUUM;")
                console.print("[green]✓ Database vacuum completed[/green]")
            else:
                console.print("[yellow]Database optimization not available for this database type[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error optimizing database: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("backup")
def backup_database(
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for backup"
    )
):
    """Create a database backup."""
    try:
        import datetime
        
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"soccer_analytics_backup_{timestamp}.sql"
        
        console.print(f"[bold blue]Creating database backup: {output_file}[/bold blue]")
        
        from soccer_analytics.config.settings import settings
        
        # Check if PostgreSQL
        if "postgresql" in settings.database_url:
            import subprocess
            
            # Extract connection details
            db_parts = settings.database_url.replace("postgresql://", "").split("/")
            db_name = db_parts[-1]
            user_host = db_parts[0].split("@")
            user_pass = user_host[0].split(":")
            host_port = user_host[1].split(":")
            
            user = user_pass[0]
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-f", output_file,
                db_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"[bold green]✓ Backup created successfully: {output_file}[/bold green]")
            else:
                console.print(f"[bold red]✗ Backup failed: {result.stderr}[/bold red]")
                raise typer.Exit(1)
        else:
            console.print("[yellow]Backup feature currently only supports PostgreSQL[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]✗ Error creating backup: {e}[/bold red]")
        raise typer.Exit(1) 