"""Utility functions for the Streamlit dashboard."""

import logging
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy.orm import Session

from soccer_analytics.config.database import get_db_session
from soccer_analytics.data_models.models import League, Team, Player, Match
from soccer_analytics.analytics.metrics import AnalyticsEngine
from soccer_analytics.analytics.calculations import AdvancedMetrics

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_leagues() -> List[Dict[str, Any]]:
    """Get all available leagues."""
    try:
        with get_db_session() as session:
            leagues = session.query(League).all()
            return [
                {
                    "id": league.id,
                    "external_id": league.external_id,
                    "name": league.name,
                    "area_name": league.area_name
                }
                for league in leagues
            ]
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        return []


@st.cache_data(ttl=300)
def get_teams(league_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get teams, optionally filtered by league."""
    try:
        with get_db_session() as session:
            query = session.query(Team)
            
            if league_id:
                query = query.filter(Team.league_id == league_id)
            
            teams = query.all()
            return [
                {
                    "id": team.id,
                    "external_id": team.external_id,
                    "name": team.name,
                    "league_name": team.league.name if team.league else "Unknown",
                    "league_id": team.league_id
                }
                for team in teams
            ]
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        return []


@st.cache_data(ttl=300)
def get_players(team_id: Optional[int] = None, position: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get players, optionally filtered by team and position."""
    try:
        with get_db_session() as session:
            query = session.query(Player)
            
            if team_id:
                query = query.filter(Player.team_id == team_id)
            
            if position:
                query = query.filter(Player.position == position)
            
            players = query.all()
            return [
                {
                    "id": player.id,
                    "external_id": player.external_id,
                    "name": player.name,
                    "position": player.position,
                    "nationality": player.nationality,
                    "team_name": player.team.name if player.team else "No Team",
                    "team_id": player.team_id
                }
                for player in players
            ]
    except Exception as e:
        logger.error(f"Error fetching players: {e}")
        return []


@st.cache_data(ttl=300)
def get_league_table(league_id: int, season_year: Optional[int] = None) -> pd.DataFrame:
    """Get league table as DataFrame."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            table_data = analytics.get_league_table(league_id, season_year)
            
            if not table_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(table_data)
            return df
    except Exception as e:
        logger.error(f"Error fetching league table: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_top_scorers(league_id: Optional[int] = None, limit: int = 10) -> pd.DataFrame:
    """Get top scorers as DataFrame."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            scorers_data = analytics.get_top_scorers(league_id, limit)
            
            if not scorers_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(scorers_data)
            return df
    except Exception as e:
        logger.error(f"Error fetching top scorers: {e}")
        return pd.DataFrame()


def create_league_table_chart(df: pd.DataFrame) -> go.Figure:
    """Create an interactive league table chart."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        return fig
    
    # Create a horizontal bar chart showing points
    fig = go.Figure()
    
    # Color scale based on position
    colors = []
    for pos in df['position']:
        if pos <= 4:  # Champions League
            colors.append('#1f77b4')  # Blue
        elif pos <= 6:  # Europa League
            colors.append('#ff7f0e')  # Orange
        elif pos >= len(df) - 2:  # Relegation
            colors.append('#d62728')  # Red
        else:
            colors.append('#2ca02c')  # Green
    
    fig.add_trace(go.Bar(
        y=df['team_name'],
        x=df['points'],
        orientation='h',
        marker_color=colors,
        text=df['points'],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                      'Position: %{customdata[0]}<br>' +
                      'Points: %{x}<br>' +
                      'Goal Difference: %{customdata[1]}<br>' +
                      'Form: %{customdata[2]}<extra></extra>',
        customdata=df[['position', 'goal_difference', 'form']].values
    ))
    
    fig.update_layout(
        title="League Table - Points",
        xaxis_title="Points",
        yaxis_title="Team",
        yaxis={'categoryorder': 'array', 'categoryarray': df['team_name'].tolist()},
        height=max(400, len(df) * 25),
        showlegend=False
    )
    
    return fig


def create_goals_distribution_chart(league_id: int) -> go.Figure:
    """Create goals distribution chart for a league."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            league_metrics = analytics.calculate_league_metrics(league_id)
            
            if not league_metrics:
                fig = go.Figure()
                fig.add_annotation(text="No data available", x=0.5, y=0.5)
                return fig
            
            # Create pie chart for match results
            labels = ['Home Wins', 'Away Wins', 'Draws']
            values = [
                league_metrics.get('home_wins', 0),
                league_metrics.get('away_wins', 0),
                league_metrics.get('draws', 0)
            ]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
            )])
            
            fig.update_layout(
                title="Match Results Distribution",
                annotations=[dict(text='Results', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            return fig
    except Exception as e:
        logger.error(f"Error creating goals distribution chart: {e}")
        return go.Figure()


def create_team_performance_radar(team_id: int, season_year: Optional[int] = None) -> go.Figure:
    """Create a radar chart showing team performance metrics."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            advanced_metrics = AdvancedMetrics(session)
            
            # Get team metrics
            team_metrics = analytics.calculate_team_metrics(team_id, season_year)
            possession_metrics = advanced_metrics.calculate_possession_metrics(team_id, season_year)
            defensive_metrics = advanced_metrics.calculate_defensive_metrics(team_id, season_year)
            
            if not team_metrics or team_metrics.get("matches_played", 0) == 0:
                fig = go.Figure()
                fig.add_annotation(text="No data available", x=0.5, y=0.5)
                return fig
            
            # Normalize metrics to 0-100 scale
            categories = [
                'Points per Game',
                'Goals per Game', 
                'Clean Sheet Rate',
                'Pass Accuracy',
                'Defensive Actions',
                'Win Rate'
            ]
            
            values = [
                min(team_metrics.get('points_per_game', 0) * 33.33, 100),  # Max 3 points per game
                min(team_metrics.get('goals_per_game', 0) * 25, 100),  # Max ~4 goals per game
                team_metrics.get('clean_sheet_rate', 0) * 100,
                possession_metrics.get('pass_accuracy', 0) * 100,
                min(defensive_metrics.get('defensive_actions_per_game', 0) * 5, 100),  # Scale defensive actions
                team_metrics.get('win_rate', 0) * 100
            ]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=team_metrics.get('team_name', 'Team'),
                line_color='rgb(1,87,155)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title=f"Performance Radar - {team_metrics.get('team_name', 'Team')}"
            )
            
            return fig
    except Exception as e:
        logger.error(f"Error creating team performance radar: {e}")
        return go.Figure()


def create_player_stats_comparison(player_ids: List[int], season_year: Optional[int] = None) -> go.Figure:
    """Create a comparison chart for multiple players."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            
            players_data = []
            for player_id in player_ids:
                stats = analytics.get_player_stats(player_id, season_year, detailed=True)
                if stats and stats.get('matches_played', 0) > 0:
                    players_data.append(stats)
            
            if not players_data:
                fig = go.Figure()
                fig.add_annotation(text="No data available", x=0.5, y=0.5)
                return fig
            
            # Create grouped bar chart
            metrics = ['goals', 'assists', 'matches_played']
            metric_names = ['Goals', 'Assists', 'Matches Played']
            
            fig = go.Figure()
            
            for i, metric in enumerate(metrics):
                fig.add_trace(go.Bar(
                    name=metric_names[i],
                    x=[player['name'] for player in players_data],
                    y=[player.get(metric, 0) for player in players_data],
                    text=[player.get(metric, 0) for player in players_data],
                    textposition='auto'
                ))
            
            fig.update_layout(
                title="Player Statistics Comparison",
                xaxis_title="Player",
                yaxis_title="Value",
                barmode='group',
                height=500
            )
            
            return fig
    except Exception as e:
        logger.error(f"Error creating player comparison chart: {e}")
        return go.Figure()


def create_match_timeline(team_id: int, limit: int = 10) -> go.Figure:
    """Create a timeline of recent matches for a team."""
    try:
        with get_db_session() as session:
            # Get recent matches
            recent_matches = session.query(Match)\
                                  .filter(
                                      (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
                                      Match.status == "FINISHED"
                                  )\
                                  .order_by(Match.utc_date.desc())\
                                  .limit(limit)\
                                  .all()
            
            if not recent_matches:
                fig = go.Figure()
                fig.add_annotation(text="No matches found", x=0.5, y=0.5)
                return fig
            
            # Prepare data
            dates = []
            results = []
            colors = []
            hover_texts = []
            
            for match in reversed(recent_matches):  # Reverse to show chronologically
                if match.home_team_id == team_id:
                    team_goals = match.score_full_time_home or 0
                    opponent_goals = match.score_full_time_away or 0
                    opponent_name = match.away_team.name
                    venue = "Home"
                else:
                    team_goals = match.score_full_time_away or 0
                    opponent_goals = match.score_full_time_home or 0
                    opponent_name = match.home_team.name
                    venue = "Away"
                
                dates.append(match.utc_date.date())
                
                # Determine result
                if team_goals > opponent_goals:
                    results.append(3)  # Win
                    colors.append('green')
                    result_text = "W"
                elif team_goals == opponent_goals:
                    results.append(1)  # Draw
                    colors.append('orange')
                    result_text = "D"
                else:
                    results.append(0)  # Loss
                    colors.append('red')
                    result_text = "L"
                
                hover_texts.append(
                    f"{result_text}: vs {opponent_name} ({venue})<br>"
                    f"Score: {team_goals}-{opponent_goals}<br>"
                    f"Date: {match.utc_date.date()}"
                )
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=results,
                mode='lines+markers',
                marker=dict(size=12, color=colors),
                line=dict(width=2, color='lightblue'),
                hovertemplate='%{text}<extra></extra>',
                text=hover_texts,
                name='Results'
            ))
            
            fig.update_layout(
                title="Recent Match Results Timeline",
                xaxis_title="Date",
                yaxis_title="Result",
                yaxis=dict(
                    tickmode='array',
                    tickvals=[0, 1, 3],
                    ticktext=['Loss', 'Draw', 'Win']
                ),
                height=400,
                showlegend=False
            )
            
            return fig
    except Exception as e:
        logger.error(f"Error creating match timeline: {e}")
        return go.Figure()


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_league_summary_stats(league_id: int) -> Dict[str, Any]:
    """Get summary statistics for a league."""
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            return analytics.calculate_league_metrics(league_id)
    except Exception as e:
        logger.error(f"Error fetching league summary stats: {e}")
        return {}


def format_large_number(number: int) -> str:
    """Format large numbers with appropriate suffixes."""
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)


def display_metric_card(title: str, value: Any, delta: Optional[str] = None, help_text: Optional[str] = None):
    """Display a metric card using Streamlit metrics."""
    if isinstance(value, float):
        if value >= 1:
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = f"{value:.3f}"
    elif isinstance(value, int):
        formatted_value = format_large_number(value)
    else:
        formatted_value = str(value)
    
    st.metric(
        label=title,
        value=formatted_value,
        delta=delta,
        help=help_text
    )


def create_goals_timeline_chart(league_id: int, season_year: Optional[int] = None) -> go.Figure:
    """Create a timeline showing goals scored over time in a league."""
    try:
        with get_db_session() as session:
            # Get matches for the league
            query = session.query(Match).filter(
                Match.competition_id == league_id,
                Match.status == "FINISHED"
            )
            
            if season_year:
                query = query.filter(
                    Match.season_start_date.isnot(None)
                ).filter(
                    Match.season_start_date >= f"{season_year}-01-01"
                ).filter(
                    Match.season_start_date < f"{season_year + 1}-01-01"
                )
            
            matches = query.order_by(Match.utc_date).all()
            
            if not matches:
                fig = go.Figure()
                fig.add_annotation(text="No matches found", x=0.5, y=0.5)
                return fig
            
            # Aggregate goals by week
            weekly_goals = {}
            for match in matches:
                week = match.utc_date.isocalendar()[1]  # Get week number
                year = match.utc_date.year
                week_key = f"{year}-W{week:02d}"
                
                total_goals = (match.score_full_time_home or 0) + (match.score_full_time_away or 0)
                
                if week_key not in weekly_goals:
                    weekly_goals[week_key] = 0
                weekly_goals[week_key] += total_goals
            
            # Sort by week
            sorted_weeks = sorted(weekly_goals.keys())
            goals_values = [weekly_goals[week] for week in sorted_weeks]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=sorted_weeks,
                y=goals_values,
                mode='lines+markers',
                name='Goals per Week',
                line=dict(width=3),
                marker=dict(size=6)
            ))
            
            # Add trend line
            if len(goals_values) > 1:
                z = pd.Series(goals_values).rolling(window=min(4, len(goals_values))).mean()
                fig.add_trace(go.Scatter(
                    x=sorted_weeks,
                    y=z,
                    mode='lines',
                    name='Trend',
                    line=dict(width=2, dash='dash'),
                    opacity=0.7
                ))
            
            fig.update_layout(
                title="Goals Scored Timeline",
                xaxis_title="Week",
                yaxis_title="Total Goals",
                height=400
            )
            
            return fig
    except Exception as e:
        logger.error(f"Error creating goals timeline: {e}")
        return go.Figure()