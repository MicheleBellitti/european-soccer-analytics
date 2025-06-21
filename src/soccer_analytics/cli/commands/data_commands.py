"""Data fetching and processing CLI commands."""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List

from soccer_analytics.etl import FootballDataFetcher, DataLoader, MAJOR_COMPETITIONS
from soccer_analytics.config.database import init_db, check_db_connection

console = Console()
app = typer.Typer()


@app.command("fetch-all")
def fetch_all_data(
    competitions: Optional[List[str]] = typer.Option(
        None,
        "--competitions",
        "-c",
        help="Specific competitions to fetch (e.g., PREMIER_LEAGUE BUNDESLIGA)"
    ),
    skip_teams: bool = typer.Option(
        False,
        "--skip-teams",
        help="Skip fetching team data"
    ),
    skip_matches: bool = typer.Option(
        False,
        "--skip-matches", 
        help="Skip fetching match data"
    ),
    skip_standings: bool = typer.Option(
        False,
        "--skip-standings",
        help="Skip fetching standings data"
    )
):
    """Fetch all data from the Football Data API."""
    try:
        console.print("[bold blue]Starting comprehensive data fetch...[/bold blue]")
        
        # Check database connection
        if not check_db_connection():
            console.print("[bold red]✗ Database connection failed[/bold red]")
            raise typer.Exit(1)
        
        # Get competition IDs
        if competitions:
            competition_ids = []
            for comp_name in competitions:
                comp_id = MAJOR_COMPETITIONS.get(comp_name.upper())
                if comp_id:
                    competition_ids.append(comp_id)
                else:
                    console.print(f"[yellow]Warning: Unknown competition '{comp_name}'[/yellow]")
        else:
            competition_ids = list(MAJOR_COMPETITIONS.values())
            console.print(f"[cyan]Fetching data for all {len(competition_ids)} major competitions[/cyan]")
        
        if not competition_ids:
            console.print("[red]No valid competitions specified[/red]")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Initialize fetcher and loader
            fetcher = FootballDataFetcher()
            loader = DataLoader()
            
            # Fetch competitions
            task = progress.add_task("Fetching competitions...", total=None)
            competitions_data = fetcher.fetch_competitions()
            created, updated = loader.load_competitions(competitions_data)
            console.print(f"[green]✓ Competitions: {created} created, {updated} updated[/green]")
            
            # Fetch teams
            if not skip_teams:
                progress.update(task, description="Fetching teams...")
                total_teams_created = 0
                total_teams_updated = 0
                
                for comp_id in competition_ids:
                    try:
                        teams = fetcher.fetch_competition_teams(comp_id)
                        # Get the league from database to get its internal ID
                        from soccer_analytics.etl.load import get_league_by_external_id
                        league_id = get_league_by_external_id(comp_id)
                        
                        if league_id:
                            created, updated = loader.load_teams(teams, league_id)
                            total_teams_created += created
                            total_teams_updated += updated
                        else:
                            console.print(f"[yellow]Warning: League not found for competition ID {comp_id}")
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to fetch teams for competition {comp_id}: {e}[/yellow]")
                        continue
                
                console.print(f"[green]✓ Teams: {total_teams_created} created, {total_teams_updated} updated[/green]")
            
            # Fetch matches
            if not skip_matches:
                progress.update(task, description="Fetching matches...")
                total_matches_created = 0
                total_matches_updated = 0
                
                for comp_id in competition_ids:
                    try:
                        matches = fetcher.fetch_competition_matches(comp_id)
                        created, updated = loader.load_matches(matches)
                        total_matches_created += created
                        total_matches_updated += updated
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to fetch matches for competition {comp_id}: {e}[/yellow]")
                        continue
                
                console.print(f"[green]✓ Matches: {total_matches_created} created, {total_matches_updated} updated[/green]")
            
            # Fetch standings
            if not skip_standings:
                progress.update(task, description="Fetching standings...")
                total_standings_created = 0
                total_standings_updated = 0
                
                for comp_id in competition_ids:
                    try:
                        standings = fetcher.fetch_competition_standings(comp_id)
                        created, updated = loader.load_standings(standings)
                        total_standings_created += created
                        total_standings_updated += updated
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to fetch standings for competition {comp_id}: {e}[/yellow]")
                        continue
                
                console.print(f"[green]✓ Standings: {total_standings_created} created, {total_standings_updated} updated[/green]")
        
        console.print("[bold green]🎉 Data fetch completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error during data fetch: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("fetch-competition")
def fetch_competition_data(
    competition: str = typer.Argument(..., help="Competition name (e.g., PREMIER_LEAGUE)"),
    include_players: bool = typer.Option(
        False,
        "--include-players",
        "-p",
        help="Also fetch player data for teams"
    )
):
    """Fetch data for a specific competition."""
    try:
        competition_id = MAJOR_COMPETITIONS.get(competition.upper())
        if not competition_id:
            console.print(f"[red]Unknown competition: {competition}[/red]")
            console.print("[cyan]Available competitions:[/cyan]")
            for comp_name in MAJOR_COMPETITIONS:
                console.print(f"  - {comp_name}")
            raise typer.Exit(1)
        
        console.print(f"[bold blue]Fetching data for {competition}...[/bold blue]")
        
        fetcher = FootballDataFetcher()
        loader = DataLoader()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Fetch competition info
            task = progress.add_task("Fetching competition...", total=None)
            competitions = fetcher.fetch_competitions()
            comp_data = [c for c in competitions if c['id'] == competition_id]
            if comp_data:
                loader.load_competitions(comp_data)
                console.print("[green]✓ Competition loaded[/green]")
            
            # Fetch teams
            progress.update(task, description="Fetching teams...")
            teams = fetcher.fetch_competition_teams(competition_id)
            
            from soccer_analytics.etl.load import get_league_by_external_id
            league_id = get_league_by_external_id(competition_id)
            
            if league_id:
                created, updated = loader.load_teams(teams, league_id)
                console.print(f"[green]✓ Teams: {created} created, {updated} updated[/green]")
                
                # Fetch players if requested
                if include_players:
                    progress.update(task, description="Fetching players...")
                    total_players_created = 0
                    total_players_updated = 0
                    
                    for team in teams:
                        try:
                            players = fetcher.fetch_team_players(team['id'])
                            from soccer_analytics.etl.load import get_team_by_external_id
                            team_id = get_team_by_external_id(team['id'])
                            
                            if team_id:
                                created, updated = loader.load_players(players, team_id)
                                total_players_created += created
                                total_players_updated += updated
                        except Exception as e:
                            console.print(f"[yellow]Warning: Failed to fetch players for {team['name']}: {e}[/yellow]")
                            continue
                    
                    console.print(f"[green]✓ Players: {total_players_created} created, {total_players_updated} updated[/green]")
            
            # Fetch matches
            progress.update(task, description="Fetching matches...")
            matches = fetcher.fetch_competition_matches(competition_id)
            created, updated = loader.load_matches(matches)
            console.print(f"[green]✓ Matches: {created} created, {updated} updated[/green]")
            
            # Fetch standings
            progress.update(task, description="Fetching standings...")
            standings = fetcher.fetch_competition_standings(competition_id)
            created, updated = loader.load_standings(standings)
            console.print(f"[green]✓ Standings: {created} created, {updated} updated[/green]")
        
        console.print(f"[bold green]🎉 {competition} data fetch completed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error fetching {competition}: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("test-api")
def test_api_connection():
    """Test Football Data API connection."""
    try:
        console.print("[bold blue]Testing Football Data API connection...[/bold blue]")
        
        fetcher = FootballDataFetcher()
        
        # Test basic connection
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Testing API connection...", total=None)
            competitions = fetcher.fetch_competitions()
            
            if competitions:
                console.print(f"[green]✓ API connection successful![/green]")
                console.print(f"[cyan]Found {len(competitions)} competitions[/cyan]")
                
                # Show first few competitions
                for i, comp in enumerate(competitions[:3]):
                    console.print(f"  {i+1}. {comp.get('name', 'Unknown')} ({comp.get('area', {}).get('name', 'Unknown')})")
                
                # Test rate limiting
                progress.update(task, description="Testing rate limits...")
                try:
                    teams = fetcher.fetch_competition_teams(2021)  # Premier League
                    console.print(f"[green]✓ Rate limiting test passed ({len(teams)} teams fetched)[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Rate limiting warning: {e}[/yellow]")
            else:
                console.print("[red]✗ No competitions returned[/red]")
                raise typer.Exit(1)
        
        console.print("[bold green]🎉 API test completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ API test failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("list-competitions")
def list_competitions():
    """List all available major competitions."""
    console.print("[bold blue]Available Major Competitions:[/bold blue]")
    
    for comp_name, comp_id in MAJOR_COMPETITIONS.items():
        console.print(f"  • [cyan]{comp_name}[/cyan] (ID: {comp_id})")
    
    console.print(f"\n[green]Total: {len(MAJOR_COMPETITIONS)} competitions available[/green]")


@app.command("status")
def data_status():
    """Show current data status in the database."""
    try:
        console.print("[bold blue]Checking data status...[/bold blue]")
        
        if not check_db_connection():
            console.print("[bold red]✗ Database connection failed[/bold red]")
            raise typer.Exit(1)
        
        from soccer_analytics.config.database import get_db_session
        from soccer_analytics.data_models.models import League, Team, Player, Match
        
        with get_db_session() as session:
            leagues_count = session.query(League).count()
            teams_count = session.query(Team).count()
            players_count = session.query(Player).count()
            matches_count = session.query(Match).count()
            
            console.print("[green]✓ Database connection successful[/green]")
            console.print(f"[cyan]Data Summary:[/cyan]")
            console.print(f"  • Leagues: {leagues_count}")
            console.print(f"  • Teams: {teams_count}")
            console.print(f"  • Players: {players_count}")
            console.print(f"  • Matches: {matches_count}")
            
            if leagues_count == 0:
                console.print("\n[yellow]⚠️  No data found. Run 'soccer-analytics data fetch-all' to populate the database.[/yellow]")
            else:
                console.print("\n[green]🎉 Database contains data and is ready for analytics![/green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error checking data status: {e}[/bold red]")
        raise typer.Exit(1) 