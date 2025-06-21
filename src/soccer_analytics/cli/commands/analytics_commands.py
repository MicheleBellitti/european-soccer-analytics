"""Analytics and metrics CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from soccer_analytics.config.database import get_db_session
from soccer_analytics.analytics.metrics import AnalyticsEngine
from soccer_analytics.analytics.calculations import AdvancedMetrics

console = Console()
app = typer.Typer()


@app.command("calculate-metrics")
def calculate_metrics(
    league_id: Optional[int] = typer.Option(
        None,
        "--league-id",
        "-l",
        help="Specific league ID to calculate metrics for"
    ),
    team_id: Optional[int] = typer.Option(
        None,
        "--team-id",
        "-t",
        help="Specific team ID to calculate metrics for"
    ),
    season_year: Optional[int] = typer.Option(
        None,
        "--season",
        "-s",
        help="Season year (e.g., 2023)"
    ),
    all_leagues: bool = typer.Option(
        False,
        "--all-leagues",
        "-a",
        help="Calculate metrics for all leagues"
    )
):
    """Calculate advanced metrics for teams and players."""
    try:
        console.print("[bold blue]Calculating advanced metrics...[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Initializing analytics engine...", total=None)
            
            with get_db_session() as session:
                analytics = AnalyticsEngine(session)
                advanced_metrics = AdvancedMetrics(session)
                
                if league_id:
                    progress.update(task, description=f"Calculating metrics for league {league_id}...")
                    league_metrics = analytics.calculate_league_metrics(league_id, season_year)
                    
                    table = Table(title=f"League {league_id} Metrics")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="magenta")
                    
                    for metric, value in league_metrics.items():
                        table.add_row(str(metric), str(value))
                    
                    console.print(table)
                    
                elif team_id:
                    progress.update(task, description=f"Calculating metrics for team {team_id}...")
                    team_metrics = analytics.calculate_team_metrics(team_id, season_year)
                    
                    table = Table(title=f"Team {team_id} Metrics")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="magenta")
                    
                    for metric, value in team_metrics.items():
                        table.add_row(str(metric), str(value))
                    
                    console.print(table)
                    
                elif all_leagues:
                    progress.update(task, description="Calculating metrics for all leagues...")
                    all_metrics = analytics.calculate_all_league_metrics(season_year)
                    
                    table = Table(title="All Leagues Metrics Summary")
                    table.add_column("League", style="cyan")
                    table.add_column("Teams", style="magenta")
                    table.add_column("Matches", style="green")
                    table.add_column("Avg Goals", style="yellow")
                    
                    for league_name, metrics in all_metrics.items():
                        table.add_row(
                            league_name,
                            str(metrics.get('teams_count', 0)),
                            str(metrics.get('matches_count', 0)),
                            f"{metrics.get('avg_goals_per_match', 0):.2f}"
                        )
                    
                    console.print(table)
                else:
                    console.print("[yellow]Please specify --league-id, --team-id, or --all-leagues[/yellow]")
                    return
        
        console.print("[bold green]✓ Metrics calculation completed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error calculating metrics: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("top-scorers")
def top_scorers(
    league_id: Optional[int] = typer.Option(
        None,
        "--league-id",
        "-l",
        help="Specific league ID"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of top scorers to show"
    ),
    season_year: Optional[int] = typer.Option(
        None,
        "--season",
        "-s",
        help="Season year"
    )
):
    """Show top goal scorers."""
    try:
        console.print("[bold blue]Fetching top scorers...[/bold blue]")
        
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            top_scorers_data = analytics.get_top_scorers(league_id, limit, season_year)
            
            table = Table(title=f"Top {limit} Goal Scorers")
            table.add_column("Rank", style="cyan")
            table.add_column("Player", style="magenta")
            table.add_column("Team", style="green")
            table.add_column("Goals", style="yellow")
            table.add_column("Assists", style="blue")
            table.add_column("Matches", style="red")
            
            for i, player in enumerate(top_scorers_data, 1):
                table.add_row(
                    str(i),
                    player['name'],
                    player['team_name'],
                    str(player['goals']),
                    str(player['assists']),
                    str(player['matches_played'])
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]✗ Error fetching top scorers: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("team-performance")
def team_performance(
    team_id: int = typer.Option(..., "--team-id", "-t", help="Team ID"),
    season_year: Optional[int] = typer.Option(
        None,
        "--season",
        "-s",
        help="Season year"
    ),
    comparison: bool = typer.Option(
        False,
        "--comparison",
        "-c",
        help="Show comparison with league average"
    )
):
    """Analyze team performance in detail."""
    try:
        console.print(f"[bold blue]Analyzing performance for team {team_id}...[/bold blue]")
        
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            performance = analytics.analyze_team_performance(team_id, season_year)
            
            # Basic performance table
            basic_table = Table(title=f"Team {team_id} Basic Performance")
            basic_table.add_column("Metric", style="cyan")
            basic_table.add_column("Value", style="magenta")
            
            basic_metrics = [
                ("Matches Played", performance.get('matches_played', 0)),
                ("Wins", performance.get('wins', 0)),
                ("Draws", performance.get('draws', 0)),
                ("Losses", performance.get('losses', 0)),
                ("Goals For", performance.get('goals_for', 0)),
                ("Goals Against", performance.get('goals_against', 0)),
                ("Goal Difference", performance.get('goal_difference', 0)),
                ("Points", performance.get('points', 0)),
            ]
            
            for metric, value in basic_metrics:
                basic_table.add_row(metric, str(value))
            
            console.print(basic_table)
            
            # Advanced metrics table
            advanced_table = Table(title="Advanced Performance Metrics")
            advanced_table.add_column("Metric", style="cyan")
            advanced_table.add_column("Value", style="magenta")
            
            advanced_metrics = [
                ("Win Rate", f"{performance.get('win_rate', 0):.1%}"),
                ("Points Per Game", f"{performance.get('points_per_game', 0):.2f}"),
                ("Goals Per Game", f"{performance.get('goals_per_game', 0):.2f}"),
                ("Goals Conceded Per Game", f"{performance.get('goals_conceded_per_game', 0):.2f}"),
                ("Clean Sheets", performance.get('clean_sheets', 0)),
                ("Clean Sheet Rate", f"{performance.get('clean_sheet_rate', 0):.1%}"),
            ]
            
            for metric, value in advanced_metrics:
                advanced_table.add_row(metric, str(value))
            
            console.print(advanced_table)
            
            if comparison:
                league_avg = analytics.get_league_averages(
                    performance.get('league_id'), season_year
                )
                
                comparison_table = Table(title="Comparison with League Average")
                comparison_table.add_column("Metric", style="cyan")
                comparison_table.add_column("Team", style="magenta")
                comparison_table.add_column("League Avg", style="green")
                comparison_table.add_column("Difference", style="yellow")
                
                comparison_metrics = [
                    ("Points Per Game", "points_per_game"),
                    ("Goals Per Game", "goals_per_game"),
                    ("Goals Conceded Per Game", "goals_conceded_per_game"),
                    ("Win Rate", "win_rate"),
                ]
                
                for metric_name, metric_key in comparison_metrics:
                    team_val = performance.get(metric_key, 0)
                    league_val = league_avg.get(metric_key, 0)
                    diff = team_val - league_val
                    
                    if metric_key == "win_rate":
                        comparison_table.add_row(
                            metric_name,
                            f"{team_val:.1%}",
                            f"{league_val:.1%}",
                            f"{diff:+.1%}"
                        )
                    else:
                        comparison_table.add_row(
                            metric_name,
                            f"{team_val:.2f}",
                            f"{league_val:.2f}",
                            f"{diff:+.2f}"
                        )
                
                console.print(comparison_table)
        
        console.print("[bold green]✓ Team performance analysis completed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error analyzing team performance: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("league-table")
def league_table(
    league_id: int = typer.Option(..., "--league-id", "-l", help="League ID"),
    season_year: Optional[int] = typer.Option(
        None,
        "--season",
        "-s",
        help="Season year"
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Number of teams to show"
    )
):
    """Display league table with current standings."""
    try:
        console.print(f"[bold blue]Fetching league table for league {league_id}...[/bold blue]")
        
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            table_data = analytics.get_league_table(league_id, season_year, limit)
            
            table = Table(title=f"League {league_id} Table")
            table.add_column("Pos", style="cyan", width=4)
            table.add_column("Team", style="magenta", min_width=20)
            table.add_column("P", style="green", width=3)
            table.add_column("W", style="green", width=3)
            table.add_column("D", style="yellow", width=3)
            table.add_column("L", style="red", width=3)
            table.add_column("GF", style="green", width=4)
            table.add_column("GA", style="red", width=4)
            table.add_column("GD", style="cyan", width=4)
            table.add_column("Pts", style="bold magenta", width=4)
            table.add_column("Form", style="blue", width=6)
            
            for team in table_data:
                # Color code position based on European competitions/relegation
                pos_style = "green" if team['position'] <= 4 else "yellow" if team['position'] <= 6 else "red" if team['position'] >= 18 else "white"
                
                table.add_row(
                    f"[{pos_style}]{team['position']}[/{pos_style}]",
                    team['team_name'],
                    str(team['played_games']),
                    str(team['won']),
                    str(team['draw']),
                    str(team['lost']),
                    str(team['goals_for']),
                    str(team['goals_against']),
                    str(team['goal_difference']),
                    str(team['points']),
                    team.get('form', 'N/A')
                )
            
            console.print(table)
        
        console.print("[bold green]✓ League table displayed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error fetching league table: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("player-stats")
def player_stats(
    player_id: int = typer.Option(..., "--player-id", "-p", help="Player ID"),
    season_year: Optional[int] = typer.Option(
        None,
        "--season",
        "-s",
        help="Season year"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed statistics"
    )
):
    """Show detailed player statistics."""
    try:
        console.print(f"[bold blue]Fetching statistics for player {player_id}...[/bold blue]")
        
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            stats = analytics.get_player_stats(player_id, season_year, detailed)
            
            # Basic info table
            info_table = Table(title=f"Player {player_id} Information")
            info_table.add_column("Attribute", style="cyan")
            info_table.add_column("Value", style="magenta")
            
            info_data = [
                ("Name", stats.get('name', 'Unknown')),
                ("Position", stats.get('position', 'Unknown')),
                ("Team", stats.get('team_name', 'Unknown')),
                ("Nationality", stats.get('nationality', 'Unknown')),
                ("Age", stats.get('age', 'Unknown')),
            ]
            
            for attr, value in info_data:
                info_table.add_row(attr, str(value))
            
            console.print(info_table)
            
            # Performance stats table
            perf_table = Table(title="Performance Statistics")
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="magenta")
            
            basic_stats = [
                ("Matches Played", stats.get('matches_played', 0)),
                ("Minutes Played", stats.get('minutes_played', 0)),
                ("Goals", stats.get('goals', 0)),
                ("Assists", stats.get('assists', 0)),
                ("Yellow Cards", stats.get('yellow_cards', 0)),
                ("Red Cards", stats.get('red_cards', 0)),
            ]
            
            for metric, value in basic_stats:
                perf_table.add_row(metric, str(value))
            
            console.print(perf_table)
            
            if detailed and stats.get('detailed_stats'):
                detailed_table = Table(title="Detailed Statistics")
                detailed_table.add_column("Metric", style="cyan")
                detailed_table.add_column("Value", style="magenta")
                
                detailed_stats = stats['detailed_stats']
                detailed_metrics = [
                    ("Shots Total", detailed_stats.get('shots_total', 0)),
                    ("Shots On Target", detailed_stats.get('shots_on_target', 0)),
                    ("Shot Accuracy", f"{detailed_stats.get('shot_accuracy', 0):.1%}"),
                    ("Passes Total", detailed_stats.get('passes_total', 0)),
                    ("Passes Completed", detailed_stats.get('passes_completed', 0)),
                    ("Pass Accuracy", f"{detailed_stats.get('pass_accuracy', 0):.1%}"),
                    ("Tackles", detailed_stats.get('tackles', 0)),
                    ("Interceptions", detailed_stats.get('interceptions', 0)),
                    ("Fouls Committed", detailed_stats.get('fouls_committed', 0)),
                    ("Fouls Drawn", detailed_stats.get('fouls_drawn', 0)),
                ]
                
                for metric, value in detailed_metrics:
                    detailed_table.add_row(metric, str(value))
                
                console.print(detailed_table)
        
        console.print("[bold green]✓ Player statistics displayed![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error fetching player statistics: {e}[/bold red]")
        raise typer.Exit(1)