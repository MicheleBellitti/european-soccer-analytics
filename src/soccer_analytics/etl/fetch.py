"""Data fetching module for European Soccer Analytics platform."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx
from httpx import Response

from soccer_analytics.config.settings import settings

logger = logging.getLogger(__name__)


class FootballDataAPIError(Exception):
    """Custom exception for Football Data API errors."""
    pass


class FootballDataFetcher:
    """Fetcher for football-data.org API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the fetcher with API key.
        
        Args:
            api_key: Football Data API key. If None, uses settings.
        """
        self.api_key = api_key or settings.football_data_api_key
        self.base_url = settings.football_data_base_url
        self.headers = {
            "X-Auth-Token": self.api_key,
            "Content-Type": "application/json"
        }
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to the API.
        
        Args:
            endpoint: API endpoint (e.g., '/competitions')
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            FootballDataAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response: Response = client.get(url, headers=self.headers, params=params)
                
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                raise FootballDataAPIError("Rate limit exceeded. Please wait before making more requests.")
            elif response.status_code == 403:
                raise FootballDataAPIError("Invalid API key or insufficient permissions.")
            else:
                raise FootballDataAPIError(f"API request failed with status {response.status_code}: {response.text}")
                
        except httpx.RequestError as e:
            raise FootballDataAPIError(f"Network error: {e}")
    
    def fetch_competitions(self, plan: str = "TIER_ONE") -> List[Dict[str, Any]]:
        """
        Fetch available competitions/leagues.
        
        Args:
            plan: Competition plan (TIER_ONE, TIER_TWO, TIER_THREE, TIER_FOUR)
            
        Returns:
            List of competition data
        """
        logger.info(f"Fetching competitions with plan: {plan}")
        
        params = {"plan": plan}
        data = self._make_request("/competitions", params)
        
        competitions = data.get("competitions", [])
        logger.info(f"Fetched {len(competitions)} competitions")
        
        return competitions
    
    def fetch_competition_teams(self, competition_id: int, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch teams for a specific competition.
        
        Args:
            competition_id: Competition ID
            season: Season year (e.g., "2023"). If None, fetches current season.
            
        Returns:
            List of team data
        """
        logger.info(f"Fetching teams for competition {competition_id}, season: {season}")
        
        endpoint = f"/competitions/{competition_id}/teams"
        params = {"season": season} if season else None
        
        data = self._make_request(endpoint, params)
        
        teams = data.get("teams", [])
        logger.info(f"Fetched {len(teams)} teams")
        
        return teams
    
    def fetch_team_players(self, team_id: int) -> List[Dict[str, Any]]:
        """
        Fetch players for a specific team.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of player data
        """
        logger.info(f"Fetching players for team {team_id}")
        
        endpoint = f"/teams/{team_id}"
        data = self._make_request(endpoint)
        
        players = data.get("squad", [])
        logger.info(f"Fetched {len(players)} players")
        
        return players
    
    def fetch_competition_matches(self, competition_id: int, season: Optional[int] = None) -> List[Dict]:
        """
        Fetch all matches for a specific competition.
        
        Args:
            competition_id: ID of the competition
            season: Year when season starts (e.g., 2024 for 2024-25 season)
            
        Returns:
            List of match dictionaries
        """
        try:
            url = f"{self.base_url}/competitions/{competition_id}/matches"
            params = {}
            if season:
                params['season'] = season
            
            response = self._make_request(url, params=params)
            matches = response.get("matches", [])
            
            logger.info(f"Fetched {len(matches)} matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []
    
    def fetch_competition_standings(self, competition_id: int, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch current standings/table for a competition.
        
        Args:
            competition_id: Competition ID
            season: Season year (e.g., "2023")
            
        Returns:
            Standings data
        """
        logger.info(f"Fetching standings for competition {competition_id}, season: {season}")
        
        endpoint = f"/competitions/{competition_id}/standings"
        params = {"season": season} if season else None
        
        data = self._make_request(endpoint, params)
        logger.info("Fetched competition standings")
        
        return data
    
    def fetch_team_matches(
        self, 
        team_id: int,
        season: Optional[str] = None,
        status: Optional[str] = None,
        venue: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch matches for a specific team.
        
        Args:
            team_id: Team ID
            season: Season year (e.g., "2023")
            status: Match status
            venue: HOME or AWAY
            limit: Maximum number of matches to return
            
        Returns:
            List of match data
        """
        logger.info(f"Fetching matches for team {team_id}")
        
        endpoint = f"/teams/{team_id}/matches"
        params = {}
        
        if season:
            params["season"] = season
        if status:
            params["status"] = status
        if venue:
            params["venue"] = venue
        if limit:
            params["limit"] = limit
            
        data = self._make_request(endpoint, params)
        
        matches = data.get("matches", [])
        logger.info(f"Fetched {len(matches)} team matches")
        
        return matches
    
    def fetch_recent_matches(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent matches across all competitions.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of recent match data
        """
        date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching recent matches from {date_from} to {date_to}")
        
        endpoint = "/matches"
        params = {
            "dateFrom": date_from,
            "dateTo": date_to
        }
        
        data = self._make_request(endpoint, params)
        
        matches = data.get("matches", [])
        logger.info(f"Fetched {len(matches)} recent matches")
        
        return matches


# Predefined competition IDs for major European leagues
MAJOR_COMPETITIONS = {
    "PREMIER_LEAGUE": 2021,  # Premier League
    "LA_LIGA": 2014,         # La Liga
    "BUNDESLIGA": 2002,      # Bundesliga
    "SERIE_A": 2019,         # Serie A
    "LIGUE_1": 2015,         # Ligue 1
    "EREDIVISIE": 2003,      # Eredivisie
    "PRIMEIRA_LIGA": 2017,   # Primeira Liga
    "CHAMPIONS_LEAGUE": 2001, # UEFA Champions League
    "EUROPA_LEAGUE": 2018,   # UEFA Europa League
}


def get_competition_id(league_name: str) -> Optional[int]:
    """
    Get competition ID by league name.
    
    Args:
        league_name: Name of the league
        
    Returns:
        Competition ID if found, None otherwise
    """
    return MAJOR_COMPETITIONS.get(league_name.upper())


def get_available_competitions() -> Dict[str, int]:
    """
    Get all available major competitions.
    
    Returns:
        Dictionary mapping competition names to IDs
    """
    return MAJOR_COMPETITIONS.copy() 