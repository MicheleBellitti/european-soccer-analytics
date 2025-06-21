"""Main Streamlit dashboard application."""

import logging
from pathlib import Path

import streamlit as st
import plotly.express as px

from soccer_analytics.config.database import check_db_connection
from soccer_analytics.config.settings import settings
from soccer_analytics.dashboard.utils import (
    get_leagues, get_league_summary_stats, display_metric_card,
    create_goals_distribution_chart, create_goals_timeline_chart
)

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="European Soccer Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# European Soccer Analytics Platform\n\nAnalyze European football data with interactive dashboards."
    }
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    h1 {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .stSelectbox > label {
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def check_system_status():
    """Check if the system is properly configured."""
    if not check_db_connection():
        st.error("❌ Database connection failed. Please check your configuration.")
        st.stop()
    
    leagues = get_leagues()
    if not leagues:
        st.warning("⚠️ No leagues found in database. Please run data fetching first.")
        st.info("Use the CLI command: `soccer-analytics data fetch-all`")
        return False
    
    return True


def main():
    """Main dashboard application."""
    st.title("⚽ European Soccer Analytics")
    st.markdown("### Welcome to the comprehensive European football data analysis platform")
    
    # Check system status
    if not check_system_status():
        return
    
    # Sidebar
    st.sidebar.title("🏆 Dashboard Navigation")
    st.sidebar.markdown("---")
    
    # League selection
    leagues = get_leagues()
    league_options = {f"{league['name']} ({league['area_name']})": league['id'] for league in leagues}
    
    if league_options:
        selected_league_name = st.sidebar.selectbox(
            "Select League",
            options=list(league_options.keys()),
            index=0,
            help="Choose a league to analyze"
        )
        selected_league_id = league_options[selected_league_name]
        
        # Get league stats
        league_stats = get_league_summary_stats(selected_league_id)
        
        if league_stats:
            st.sidebar.markdown("### 📊 Quick Stats")
            st.sidebar.metric("Total Matches", league_stats.get('total_matches', 0))
            st.sidebar.metric("Total Goals", league_stats.get('total_goals', 0))
            st.sidebar.metric("Avg Goals/Match", f"{league_stats.get('avg_goals_per_match', 0):.2f}")
    else:
        st.error("No leagues available. Please fetch data first.")
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Quick Actions")
    
    if st.sidebar.button("🔄 Refresh Data", help="Refresh cached data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content
    if league_stats:
        # Overview metrics
        st.markdown("## 📈 League Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            display_metric_card(
                "Total Teams",
                league_stats.get('teams_count', 0),
                help_text="Number of teams in the league"
            )
        
        with col2:
            display_metric_card(
                "Total Players",
                league_stats.get('players_count', 0),
                help_text="Total players across all teams"
            )
        
        with col3:
            display_metric_card(
                "Finished Matches",
                league_stats.get('finished_matches', 0),
                help_text="Completed matches this season"
            )
        
        with col4:
            display_metric_card(
                "Goals per Match",
                league_stats.get('avg_goals_per_match', 0),
                help_text="Average goals scored per match"
            )
        
        # Charts
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Match Results Distribution")
            results_chart = create_goals_distribution_chart(selected_league_id)
            st.plotly_chart(results_chart, use_container_width=True)
        
        with col2:
            st.markdown("### 📅 Goals Timeline")
            timeline_chart = create_goals_timeline_chart(selected_league_id)
            st.plotly_chart(timeline_chart, use_container_width=True)
        
        # Additional metrics
        st.markdown("---")
        st.markdown("### 🏠 Home vs Away Performance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            display_metric_card(
                "Home Win %",
                f"{league_stats.get('home_win_percentage', 0):.1f}%",
                help_text="Percentage of matches won by home teams"
            )
        
        with col2:
            display_metric_card(
                "Away Win %",
                f"{league_stats.get('away_win_percentage', 0):.1f}%",
                help_text="Percentage of matches won by away teams"
            )
        
        with col3:
            display_metric_card(
                "Draw %",
                f"{league_stats.get('draw_percentage', 0):.1f}%",
                help_text="Percentage of matches ending in draws"
            )
        
        # High-scoring matches
        st.markdown("---")
        st.markdown("### ⚡ Match Intensity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            display_metric_card(
                "High-Scoring Matches",
                league_stats.get('high_scoring_matches', 0),
                help_text="Matches with 3+ goals"
            )
        
        with col2:
            display_metric_card(
                "Clean Sheets",
                league_stats.get('clean_sheets', 0),
                help_text="Matches where one team didn't score"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; margin-top: 2rem;'>
        <p>European Soccer Analytics Platform | Built with Streamlit & Python</p>
        <p>Data sources: Football Data API | Real-time analytics for European football</p>
    </div>
    """, unsafe_allow_html=True)


def sidebar_info():
    """Display information in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown("""
    This dashboard provides comprehensive analytics for European football leagues:
    
    - **League Overview**: Key metrics and trends
    - **Team Analysis**: Detailed team performance
    - **Player Search**: Individual player statistics
    
    Navigate using the menu above to explore different views.
    """)
    
    st.sidebar.markdown("### 🛠️ System Status")
    if check_db_connection():
        st.sidebar.success("✅ Database: Connected")
    else:
        st.sidebar.error("❌ Database: Disconnected")
    
    leagues_count = len(get_leagues())
    st.sidebar.info(f"📊 {leagues_count} leagues available")


if __name__ == "__main__":
    # Add sidebar info
    sidebar_info()
    
    # Run main application
    main()