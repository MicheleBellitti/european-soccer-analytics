"""League Overview dashboard page."""

import streamlit as st
import pandas as pd
import plotly.express as px

from soccer_analytics.dashboard.utils import (
    get_leagues, get_league_table, get_top_scorers, get_league_summary_stats,
    create_league_table_chart, display_metric_card, create_goals_timeline_chart
)

# Page configuration
st.set_page_config(
    page_title="League Overview - European Soccer Analytics",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .league-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .standings-table {
        font-size: 0.9em;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main league overview page."""
    st.title("🏆 League Overview")
    st.markdown("### Comprehensive league statistics and standings")
    
    # Sidebar filters
    st.sidebar.title("🔧 Filters")
    
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
    
    # Season filter (placeholder for future implementation)
    st.sidebar.selectbox(
        "Season",
        options=["2023-24", "2022-23"],
        index=0,
        disabled=True,
        help="Season filtering will be available in future updates"
    )
    
    # Display options
    st.sidebar.markdown("### 📊 Display Options")
    show_full_table = st.sidebar.checkbox("Show Full League Table", value=True)
    show_top_scorers = st.sidebar.checkbox("Show Top Scorers", value=True)
    show_charts = st.sidebar.checkbox("Show Charts", value=True)
    
    # Main content
    league_stats = get_league_summary_stats(selected_league_id)
    
    if not league_stats:
        st.warning("No data available for the selected league.")
        return
    
    # League header
    selected_league = next(l for l in leagues if l['id'] == selected_league_id)
    st.markdown(f"""
    <div class="league-header">
        <h2>🏆 {selected_league['name']}</h2>
        <p><strong>Region:</strong> {selected_league['area_name']} | 
           <strong>Season:</strong> Current | 
           <strong>Status:</strong> Active</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    st.markdown("## 📈 League Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        display_metric_card(
            "Teams",
            league_stats.get('teams_count', 0),
            help_text="Number of teams in the league"
        )
    
    with col2:
        display_metric_card(
            "Matches Played",
            league_stats.get('finished_matches', 0),
            help_text="Completed matches this season"
        )
    
    with col3:
        display_metric_card(
            "Total Goals",
            league_stats.get('total_goals', 0),
            help_text="Goals scored across all matches"
        )
    
    with col4:
        display_metric_card(
            "Goals/Match",
            league_stats.get('avg_goals_per_match', 0),
            help_text="Average goals per match"
        )
    
    with col5:
        display_metric_card(
            "Home Win %",
            f"{league_stats.get('home_win_percentage', 0):.1f}%",
            help_text="Percentage of home wins"
        )
    
    # Charts section
    if show_charts:
        st.markdown("---")
        st.markdown("## 📊 League Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Goals Timeline")
            timeline_chart = create_goals_timeline_chart(selected_league_id)
            st.plotly_chart(timeline_chart, use_container_width=True)
        
        with col2:
            st.markdown("### Match Results Distribution")
            
            # Create results pie chart
            results_data = {
                'Result': ['Home Wins', 'Away Wins', 'Draws'],
                'Count': [
                    league_stats.get('home_wins', 0),
                    league_stats.get('away_wins', 0),
                    league_stats.get('draws', 0)
                ]
            }
            results_df = pd.DataFrame(results_data)
            
            if not results_df['Count'].sum() == 0:
                fig = px.pie(
                    results_df,
                    values='Count',
                    names='Result',
                    title="Match Outcomes",
                    color_discrete_map={
                        'Home Wins': '#1f77b4',
                        'Away Wins': '#ff7f0e',
                        'Draws': '#2ca02c'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No match results available for charts")
    
    # League table
    if show_full_table:
        st.markdown("---")
        st.markdown("## 📋 League Table")
        
        table_df = get_league_table(selected_league_id)
        
        if not table_df.empty:
            # Interactive table
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Current Standings")
                
                # Format the dataframe for display
                display_df = table_df.copy()
                display_df = display_df.rename(columns={
                    'position': 'Pos',
                    'team_name': 'Team',
                    'played_games': 'P',
                    'won': 'W',
                    'draw': 'D',
                    'lost': 'L',
                    'goals_for': 'GF',
                    'goals_against': 'GA',
                    'goal_difference': 'GD',
                    'points': 'Pts',
                    'form': 'Form'
                })
                
                # Apply styling
                styled_df = display_df.style.apply(
                    lambda x: ['background-color: #e8f4fd' if x.name < 4  # Champions League
                              else 'background-color: #fff2e8' if x.name < 6  # Europa League
                              else 'background-color: #fde8e8' if x.name >= len(x) - 3  # Relegation
                              else '' for _ in x], axis=1
                )
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Legend
                st.markdown("""
                <div style='font-size: 0.8em; margin-top: 0.5rem;'>
                    <span style='background-color: #e8f4fd; padding: 2px 8px; border-radius: 3px;'>🏆 Champions League</span>
                    <span style='background-color: #fff2e8; padding: 2px 8px; border-radius: 3px; margin-left: 0.5rem;'>🥈 Europa League</span>
                    <span style='background-color: #fde8e8; padding: 2px 8px; border-radius: 3px; margin-left: 0.5rem;'>⬇️ Relegation</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### Points Visualization")
                points_chart = create_league_table_chart(table_df)
                st.plotly_chart(points_chart, use_container_width=True)
        else:
            st.info("League table data not available")
    
    # Top scorers
    if show_top_scorers:
        st.markdown("---")
        st.markdown("## ⚽ Top Scorers")
        
        scorers_df = get_top_scorers(selected_league_id, limit=10)
        
        if not scorers_df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Format scorers table
                display_scorers = scorers_df.copy()
                display_scorers['rank'] = range(1, len(display_scorers) + 1)
                display_scorers = display_scorers[['rank', 'name', 'team_name', 'goals', 'assists', 'matches_played']]
                display_scorers.columns = ['Rank', 'Player', 'Team', 'Goals', 'Assists', 'Matches']
                
                st.dataframe(
                    display_scorers,
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                # Top scorers chart
                top_10_scorers = scorers_df.head(10)
                fig = px.bar(
                    top_10_scorers,
                    x='goals',
                    y='name',
                    orientation='h',
                    title="Goals Scored",
                    labels={'goals': 'Goals', 'name': 'Player'},
                    color='goals',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Top scorers data not available")
    
    # Additional stats
    st.markdown("---")
    st.markdown("## 🔍 Additional Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Offensive Stats")
        display_metric_card("High-Scoring Matches", league_stats.get('high_scoring_matches', 0))
        display_metric_card("Total Players", league_stats.get('players_count', 0))
    
    with col2:
        st.markdown("#### Defensive Stats") 
        display_metric_card("Clean Sheets", league_stats.get('clean_sheets', 0))
        display_metric_card("Clean Sheet %", f"{league_stats.get('clean_sheet_percentage', 0):.1f}%")
    
    with col3:
        st.markdown("#### Match Distribution")
        display_metric_card("Away Win %", f"{league_stats.get('away_win_percentage', 0):.1f}%")
        display_metric_card("Draw %", f"{league_stats.get('draw_percentage', 0):.1f}%")
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()