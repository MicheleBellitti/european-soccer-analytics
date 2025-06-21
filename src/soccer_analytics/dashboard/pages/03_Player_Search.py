"""Player Search and Analysis dashboard page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

from soccer_analytics.dashboard.utils import (
    get_leagues, get_teams, get_players, get_top_scorers,
    create_player_stats_comparison, display_metric_card
)
from soccer_analytics.config.database import get_db_session
from soccer_analytics.analytics.metrics import AnalyticsEngine
from soccer_analytics.analytics.calculations import AdvancedMetrics
from soccer_analytics.data_models.models import Player, Team, PlayerStats, Match
from soccer_analytics.dashboard.utils import get_teams_by_league

# Page configuration
st.set_page_config(
    page_title="Player Search - European Soccer Analytics",
    page_icon="⚽",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .player-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    }
    .player-name {
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .player-info {
        font-size: 1.2em;
        opacity: 0.9;
    }
    .stat-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: all 0.3s;
        height: 100%;
    }
    .stat-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    }
    .stat-number {
        font-size: 3em;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 1em;
        color: #666;
        margin-top: 5px;
    }
    .position-indicator {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 25px;
        font-weight: bold;
        margin: 10px 5px;
    }
    .pos-goalkeeper { background: #e74c3c; color: white; }
    .pos-defence { background: #3498db; color: white; }
    .pos-midfield { background: #2ecc71; color: white; }
    .pos-offence { background: #f39c12; color: white; }
    .search-container {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .player-list-item {
        background: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        cursor: pointer;
        transition: all 0.2s;
    }
    .player-list-item:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<h1 style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
           -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
    ⚽ Player Search & Analytics
</h1>
""", unsafe_allow_html=True)

# Search interface
st.markdown("<div class='search-container'>", unsafe_allow_html=True)

search_method = st.radio(
    "Search Method",
    ["🔍 Search by Name", "🏟️ Browse by Team", "🌟 Top Performers"],
    horizontal=True
)

st.markdown("</div>", unsafe_allow_html=True)

# Initialize selected player
selected_player = None

if search_method == "🔍 Search by Name":
    player_name = st.text_input("Enter player name", placeholder="e.g., Mohamed Salah")
    
    if player_name:
        with get_db_session() as session:
            players = session.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).limit(10).all()
            
            if players:
                st.markdown("### Search Results")
                cols = st.columns(2)
                for idx, player in enumerate(players):
                    with cols[idx % 2]:
                        if st.button(f"{player.name} ({player.position or 'Unknown'})", key=f"player_{player.id}"):
                            selected_player = player

elif search_method == "🏟️ Browse by Team":
    col1, col2 = st.columns(2)
    
    with col1:
        leagues = get_leagues()
        if leagues:
            league_options = [(league['id'], league['name']) if isinstance(league, dict) else (league.id, league.name) for league in leagues]
            selected_league_id = st.selectbox(
                "Select League",
                options=[lid for lid, _ in league_options],
                format_func=lambda x: next(name for lid, name in league_options if lid == x)
            )
    
    with col2:
        if selected_league_id:
            teams = get_teams_by_league(selected_league_id)
            selected_team = st.selectbox(
                "Select Team",
                options=teams,
                format_func=lambda x: x.name
            )
            
            if selected_team:
                with get_db_session() as session:
                    players = session.query(Player).filter(
                        Player.team_id == selected_team.id
                    ).order_by(Player.position, Player.name).all()
                    
                    if players:
                        st.markdown(f"### {selected_team.name} Squad")
                        
                        # Group by position
                        positions = {}
                        for player in players:
                            pos = player.position or 'Unknown'
                            if pos not in positions:
                                positions[pos] = []
                            positions[pos].append(player)
                        
                        for position, position_players in positions.items():
                            st.markdown(f"#### {position}")
                            cols = st.columns(3)
                            for idx, player in enumerate(position_players):
                                with cols[idx % 3]:
                                    if st.button(
                                        f"{player.name}\n#{player.shirt_number or '-'}",
                                        key=f"team_player_{player.id}"
                                    ):
                                        selected_player = player

elif search_method == "🌟 Top Performers":
    metric = st.selectbox(
        "Select Metric",
        ["Goals", "Assists", "Matches Played", "Minutes Played"]
    )
    
    with get_db_session() as session:
        # For demo purposes, show all players sorted by position
        players = session.query(Player).order_by(Player.position).limit(20).all()
        
        if players:
            st.markdown(f"### Top Players")
            
            for idx, player in enumerate(players):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    if st.button(
                        f"{idx+1}. {player.name}",
                        key=f"top_player_{player.id}"
                    ):
                        selected_player = player
                
                with col2:
                    st.markdown(f"**{player.position or 'N/A'}**")
                
                with col3:
                    team = session.query(Team).filter(Team.id == player.team_id).first()
                    st.markdown(f"*{team.name if team else 'N/A'}*")

# Display selected player details
if selected_player:
    st.markdown("---")
    
    # Player hero section
    with get_db_session() as session:
        team = session.query(Team).filter(Team.id == selected_player.team_id).first()
        
        # Get player statistics
        player_stats = session.query(PlayerStats).filter(
            PlayerStats.player_id == selected_player.id
        ).all()
    
    st.markdown(f"""
    <div class='player-hero'>
        <div class='player-name'>{selected_player.name}</div>
        <div class='player-info'>
            <span class='position-indicator pos-{(selected_player.position or 'unknown').lower()}'>{selected_player.position or 'Unknown'}</span>
            #{selected_player.shirt_number or '-'} | {team.name if team else 'Free Agent'} | 
            Age: {datetime.now().year - selected_player.date_of_birth.year if selected_player.date_of_birth else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Performance", "🎯 Heat Maps", "🆚 Compare"])
    
    with tab1:
        # Basic statistics
        st.markdown("### 📊 Season Statistics")
        
        # Calculate aggregated stats
        total_goals = sum(stat.goals or 0 for stat in player_stats)
        total_assists = sum(stat.assists or 0 for stat in player_stats)
        total_matches = len(player_stats)
        total_minutes = sum(stat.minutes_played or 0 for stat in player_stats)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{total_goals}</div>
                <div class='stat-label'>Goals</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{total_assists}</div>
                <div class='stat-label'>Assists</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{total_matches}</div>
                <div class='stat-label'>Matches</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{total_minutes}</div>
                <div class='stat-label'>Minutes</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Additional stats if available
        if player_stats:
            st.markdown("### 🎯 Advanced Metrics")
            
            total_shots = sum(stat.shots or 0 for stat in player_stats)
            total_passes = sum(stat.passes_completed or 0 for stat in player_stats)
            total_tackles = sum(stat.tackles or 0 for stat in player_stats)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_rating = np.mean([stat.rating for stat in player_stats if stat.rating]) if any(stat.rating for stat in player_stats) else 0
                st.metric("Average Rating", f"{avg_rating:.1f}" if avg_rating else "N/A")
            
            with col2:
                goals_per_90 = (total_goals / total_minutes * 90) if total_minutes > 0 else 0
                st.metric("Goals per 90 min", f"{goals_per_90:.2f}")
            
            with col3:
                shot_accuracy = (total_goals / total_shots * 100) if total_shots > 0 else 0
                st.metric("Shot Accuracy", f"{shot_accuracy:.1f}%")
    
    with tab2:
        st.markdown("### 📈 Performance Analysis")
        
        if player_stats and len(player_stats) > 1:
            # Create performance timeline
            perf_data = []
            for stat in sorted(player_stats, key=lambda x: x.match_id):
                with get_db_session() as session:
                    match = session.query(Match).filter(Match.id == stat.match_id).first()
                    if match:
                        perf_data.append({
                            'Date': match.utc_date,
                            'Goals': stat.goals or 0,
                            'Assists': stat.assists or 0,
                            'Rating': stat.rating or 0,
                            'Minutes': stat.minutes_played or 0
                        })
            
            if perf_data:
                perf_df = pd.DataFrame(perf_data)
                
                # Goals and assists over time
                fig_timeline = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Goals & Assists Timeline', 'Performance Rating'),
                    row_heights=[0.6, 0.4]
                )
                
                fig_timeline.add_trace(
                    go.Scatter(
                        x=perf_df['Date'],
                        y=perf_df['Goals'],
                        mode='lines+markers',
                        name='Goals',
                        line=dict(color='#e74c3c', width=3)
                    ),
                    row=1, col=1
                )
                
                fig_timeline.add_trace(
                    go.Scatter(
                        x=perf_df['Date'],
                        y=perf_df['Assists'],
                        mode='lines+markers',
                        name='Assists',
                        line=dict(color='#3498db', width=3)
                    ),
                    row=1, col=1
                )
                
                fig_timeline.add_trace(
                    go.Scatter(
                        x=perf_df['Date'],
                        y=perf_df['Rating'],
                        mode='lines+markers',
                        name='Rating',
                        line=dict(color='#2ecc71', width=3),
                        fill='tozeroy'
                    ),
                    row=2, col=1
                )
                
                fig_timeline.update_layout(height=600, showlegend=True)
                st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("Not enough match data available for performance timeline.")
    
    with tab3:
        st.markdown("### 🎯 Performance Heat Map")
        
        # Create a mock heat map for player performance areas
        if selected_player.position in ['Midfield', 'Offence']:
            # Attacking heat map
            categories = ['Shooting', 'Dribbling', 'Passing', 'Pace', 'Physical']
            values = [
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95)
            ]
        else:
            # Defensive heat map
            categories = ['Defending', 'Physical', 'Passing', 'Pace', 'Aerial']
            values = [
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95),
                np.random.randint(60, 95)
            ]
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=selected_player.name,
            fillcolor='rgba(102, 126, 234, 0.5)',
            line=dict(color='#667eea', width=2)
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title=f"{selected_player.name} - Skill Radar",
            height=500
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with tab4:
        st.markdown("### 🆚 Player Comparison")
        
        # Select another player to compare
        with get_db_session() as session:
            other_players = session.query(Player).filter(
                Player.id != selected_player.id,
                Player.position == selected_player.position
            ).limit(20).all()
        
        if other_players:
            compare_player = st.selectbox(
                "Select player to compare",
                options=other_players,
                format_func=lambda x: f"{x.name} ({x.position})"
            )
            
            if compare_player:
                # Get stats for comparison
                with get_db_session() as session:
                    compare_stats = session.query(PlayerStats).filter(
                        PlayerStats.player_id == compare_player.id
                    ).all()
                
                # Calculate comparison metrics
                compare_goals = sum(stat.goals or 0 for stat in compare_stats)
                compare_assists = sum(stat.assists or 0 for stat in compare_stats)
                compare_matches = len(compare_stats)
                
                # Comparison chart
                fig_compare = go.Figure()
                
                categories = ['Goals', 'Assists', 'Matches', 'Goals/Match', 'Assists/Match']
                
                player1_values = [
                    total_goals,
                    total_assists,
                    total_matches,
                    total_goals/total_matches if total_matches > 0 else 0,
                    total_assists/total_matches if total_matches > 0 else 0
                ]
                
                player2_values = [
                    compare_goals,
                    compare_assists,
                    compare_matches,
                    compare_goals/compare_matches if compare_matches > 0 else 0,
                    compare_assists/compare_matches if compare_matches > 0 else 0
                ]
                
                fig_compare.add_trace(go.Bar(
                    name=selected_player.name,
                    x=categories,
                    y=player1_values,
                    marker_color='#667eea'
                ))
                
                fig_compare.add_trace(go.Bar(
                    name=compare_player.name,
                    x=categories,
                    y=player2_values,
                    marker_color='#764ba2'
                ))
                
                fig_compare.update_layout(
                    title="Player Comparison",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig_compare, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Player Search & Analytics | European Soccer Analytics Platform</p>",
    unsafe_allow_html=True
) 