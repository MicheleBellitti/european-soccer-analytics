"""Team Analysis dashboard page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from soccer_analytics.dashboard.utils import (
    get_leagues, get_teams, get_players, get_league_table,
    create_team_performance_radar, create_match_timeline,
    display_metric_card, get_league_summary_stats
)
from soccer_analytics.config.database import get_db_session
from soccer_analytics.analytics.metrics import AnalyticsEngine
from soccer_analytics.analytics.calculations import AdvancedMetrics

# Page configuration
st.set_page_config(
    page_title="Team Analysis - European Soccer Analytics",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .team-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .squad-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main team analysis page."""
    st.title("🏟️ Team Analysis")
    st.markdown("### Detailed team performance, squad, and match analysis")
    
    # Sidebar filters
    st.sidebar.title("🔧 Team Selection")
    
    # League selection
    leagues = get_leagues()
    if not leagues:
        st.error("No leagues available. Please fetch data first.")
        return
    
    league_options = {f"{league['name']} ({league['area_name']})": league['id'] for league in leagues}
    selected_league_name = st.sidebar.selectbox(
        "Select League",
        options=list(league_options.keys()),
        index=0
    )
    selected_league_id = league_options[selected_league_name]
    
    # Team selection
    teams = get_teams(selected_league_id)
    if not teams:
        st.warning("No teams available for the selected league.")
        return
    
    team_options = {team['name']: team['id'] for team in teams}
    selected_team_name = st.sidebar.selectbox(
        "Select Team",
        options=list(team_options.keys()),
        index=0
    )
    selected_team_id = team_options[selected_team_name]
    
    # Analysis options
    st.sidebar.markdown("### 📊 Analysis Options")
    show_performance = st.sidebar.checkbox("Performance Metrics", value=True)
    show_squad = st.sidebar.checkbox("Squad Analysis", value=True)
    show_matches = st.sidebar.checkbox("Recent Matches", value=True)
    show_comparison = st.sidebar.checkbox("League Comparison", value=False)
    
    # Main content
    selected_team = next(team for team in teams if team['id'] == selected_team_id)
    
    # Team header
    st.markdown(f"""
    <div class="team-header">
        <h2>🏟️ {selected_team['name']}</h2>
        <p><strong>League:</strong> {selected_team['league_name']} | 
           <strong>Analysis:</strong> Current Season Performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get team analytics
    try:
        with get_db_session() as session:
            analytics = AnalyticsEngine(session)
            advanced_metrics = AdvancedMetrics(session)
            
            # Get team performance data
            team_metrics = analytics.calculate_team_metrics(selected_team_id)
            
            if not team_metrics or team_metrics.get("matches_played", 0) == 0:
                st.warning("No performance data available for this team.")
                return
            
            # Performance metrics section
            if show_performance:
                st.markdown("## 📈 Performance Overview")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    display_metric_card(
                        "Matches Played",
                        team_metrics.get('matches_played', 0),
                        help_text="Total matches played this season"
                    )
                
                with col2:
                    display_metric_card(
                        "Points",
                        team_metrics.get('points', 0),
                        help_text="Total points earned"
                    )
                
                with col3:
                    display_metric_card(
                        "Win Rate",
                        f"{team_metrics.get('win_rate', 0):.1%}",
                        help_text="Percentage of matches won"
                    )
                
                with col4:
                    display_metric_card(
                        "Goals Scored",
                        team_metrics.get('goals_for', 0),
                        help_text="Total goals scored"
                    )
                
                with col5:
                    display_metric_card(
                        "Goal Difference",
                        f"{team_metrics.get('goal_difference', 0):+d}",
                        help_text="Goals for minus goals against"
                    )
                
                # Advanced metrics
                st.markdown("### 🎯 Advanced Metrics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Performance radar chart
                    st.markdown("#### Performance Radar")
                    radar_chart = create_team_performance_radar(selected_team_id)
                    st.plotly_chart(radar_chart, use_container_width=True)
                
                with col2:
                    # Additional metrics
                    st.markdown("#### Key Statistics")
                    
                    metrics_col1, metrics_col2 = st.columns(2)
                    
                    with metrics_col1:
                        display_metric_card("Points per Game", f"{team_metrics.get('points_per_game', 0):.2f}")
                        display_metric_card("Goals per Game", f"{team_metrics.get('goals_per_game', 0):.2f}")
                        display_metric_card("Clean Sheets", team_metrics.get('clean_sheets', 0))
                    
                    with metrics_col2:
                        display_metric_card("Goals Conceded", team_metrics.get('goals_against', 0))
                        display_metric_card("Clean Sheet Rate", f"{team_metrics.get('clean_sheet_rate', 0):.1%}")
                        
                        # Form display
                        wins = team_metrics.get('wins', 0)
                        draws = team_metrics.get('draws', 0)
                        losses = team_metrics.get('losses', 0)
                        st.metric("Record", f"{wins}W-{draws}D-{losses}L")
            
            # Squad analysis section
            if show_squad:
                st.markdown("---")
                st.markdown("## 👥 Squad Analysis")
                
                players = get_players(selected_team_id)
                
                if players:
                    # Squad overview
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("### Squad List")
                        
                        # Create squad DataFrame
                        squad_df = pd.DataFrame(players)
                        squad_df = squad_df[['name', 'position', 'nationality']].copy()
                        squad_df.columns = ['Player', 'Position', 'Nationality']
                        
                        # Position filter
                        positions = ['All'] + list(squad_df['Position'].dropna().unique())
                        selected_position = st.selectbox("Filter by Position", positions)
                        
                        if selected_position != 'All':
                            filtered_df = squad_df[squad_df['Position'] == selected_position]
                        else:
                            filtered_df = squad_df
                        
                        st.dataframe(
                            filtered_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.markdown("### Squad Stats")
                        
                        # Squad composition
                        total_players = len(players)
                        display_metric_card("Total Players", total_players)
                        
                        # Position breakdown
                        if not squad_df.empty:
                            position_counts = squad_df['Position'].value_counts()
                            
                            fig = px.pie(
                                values=position_counts.values,
                                names=position_counts.index,
                                title="Squad by Position",
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Nationality breakdown
                        if not squad_df.empty and 'Nationality' in squad_df.columns:
                            nationality_counts = squad_df['Nationality'].value_counts().head(5)
                            
                            if len(nationality_counts) > 0:
                                st.markdown("#### Top Nationalities")
                                for nat, count in nationality_counts.items():
                                    st.write(f"🌍 {nat}: {count} players")
                else:
                    st.info("No squad information available for this team.")
            
            # Recent matches section
            if show_matches:
                st.markdown("---")
                st.markdown("## ⚽ Recent Matches")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### Match Timeline")
                    timeline_chart = create_match_timeline(selected_team_id, limit=10)
                    st.plotly_chart(timeline_chart, use_container_width=True)
                
                with col2:
                    st.markdown("### Home vs Away")
                    
                    # Get home/away performance
                    home_performance = team_metrics.get('home_performance', {})
                    away_performance = team_metrics.get('away_performance', {})
                    
                    if home_performance and away_performance:
                        # Home stats
                        st.markdown("#### 🏠 Home Performance")
                        display_metric_card("Home Wins", home_performance.get('wins', 0))
                        display_metric_card("Home Points/Game", f"{home_performance.get('points_per_game', 0):.2f}")
                        
                        # Away stats
                        st.markdown("#### ✈️ Away Performance")
                        display_metric_card("Away Wins", away_performance.get('wins', 0))
                        display_metric_card("Away Points/Game", f"{away_performance.get('points_per_game', 0):.2f}")
                    else:
                        st.info("Home/Away breakdown not available")
            
            # League comparison section
            if show_comparison:
                st.markdown("---")
                st.markdown("## 📊 League Comparison")
                
                # Get league table for context
                league_table = get_league_table(selected_league_id)
                
                if not league_table.empty:
                    team_position = league_table[league_table['team_name'] == selected_team['name']]
                    
                    if not team_position.empty:
                        current_position = team_position.iloc[0]['position']
                        total_teams = len(league_table)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### League Position")
                            display_metric_card("Current Position", f"{current_position} / {total_teams}")
                            
                            # Position visualization
                            position_percentile = (total_teams - current_position + 1) / total_teams * 100
                            
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = position_percentile,
                                title = {'text': "League Percentile"},
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                gauge = {
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "darkblue"},
                                    'steps': [
                                        {'range': [0, 25], 'color': "lightgray"},
                                        {'range': [25, 75], 'color': "gray"},
                                        {'range': [75, 100], 'color': "lightgreen"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 90
                                    }
                                }
                            ))
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.markdown("### Performance vs League Average")
                            
                            # Get league averages
                            league_avg = analytics.get_league_averages(selected_league_id)
                            
                            if league_avg:
                                comparison_data = []
                                metrics_to_compare = [
                                    ("Points per Game", "points_per_game"),
                                    ("Goals per Game", "goals_per_game"),
                                    ("Win Rate", "win_rate")
                                ]
                                
                                for metric_name, metric_key in metrics_to_compare:
                                    team_val = team_metrics.get(metric_key, 0)
                                    league_val = league_avg.get(metric_key, 0)
                                    diff = team_val - league_val
                                    
                                    comparison_data.append({
                                        'Metric': metric_name,
                                        'Team': team_val,
                                        'League Avg': league_val,
                                        'Difference': diff
                                    })
                                
                                comparison_df = pd.DataFrame(comparison_data)
                                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                else:
                    st.info("League comparison data not available")
    
    except Exception as e:
        st.error(f"Error loading team analysis: {e}")
        st.info("Please ensure the database is populated with team data.")
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Team Data", type="primary"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main() 