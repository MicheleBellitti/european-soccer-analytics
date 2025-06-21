"""Unit tests for ETL functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from soccer_analytics.etl.fetch import FootballDataFetcher, FootballDataAPIError
from soccer_analytics.etl.load import DataLoader


class TestFootballDataFetcher:
    """Test cases for FootballDataFetcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = FootballDataFetcher(api_key="test_key")
    
    def test_init(self):
        """Test fetcher initialization."""
        assert self.fetcher.api_key == "test_key"
        assert self.fetcher.base_url == "https://api.football-data.org/v4"
        assert "X-Auth-Token" in self.fetcher.headers
    
    @patch('soccer_analytics.etl.fetch.httpx.Client')
    def test_make_request_success(self, mock_client):
        """Test successful API request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        
        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context
        
        result = self.fetcher._make_request("/test")
        
        assert result == {"test": "data"}
        mock_client.assert_called_once()
    
    @patch('soccer_analytics.etl.fetch.httpx.Client')
    def test_make_request_rate_limit(self, mock_client):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context
        
        with pytest.raises(FootballDataAPIError, match="Rate limit exceeded"):
            self.fetcher._make_request("/test")
    
    @patch('soccer_analytics.etl.fetch.httpx.Client')
    def test_make_request_auth_error(self, mock_client):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        
        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context
        
        with pytest.raises(FootballDataAPIError, match="Invalid API key"):
            self.fetcher._make_request("/test")
    
    @patch.object(FootballDataFetcher, '_make_request')
    def test_fetch_competitions(self, mock_request):
        """Test fetching competitions."""
        mock_request.return_value = {
            "competitions": [
                {"id": 1, "name": "Test League", "area": {"name": "Test Country"}}
            ]
        }
        
        result = self.fetcher.fetch_competitions()
        
        assert len(result) == 1
        assert result[0]["name"] == "Test League"
        mock_request.assert_called_once_with("/competitions", {"plan": "TIER_ONE"})
    
    @patch.object(FootballDataFetcher, '_make_request')
    def test_fetch_competition_teams(self, mock_request):
        """Test fetching teams for a competition."""
        mock_request.return_value = {
            "teams": [
                {"id": 1, "name": "Test Team", "area": {"name": "Test Country"}}
            ]
        }
        
        result = self.fetcher.fetch_competition_teams(123, "2023")
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Team"
        mock_request.assert_called_once_with("/competitions/123/teams", {"season": "2023"})
    
    @patch.object(FootballDataFetcher, '_make_request')
    def test_fetch_team_players(self, mock_request):
        """Test fetching players for a team."""
        mock_request.return_value = {
            "squad": [
                {"id": 1, "name": "Test Player", "position": "Midfielder"}
            ]
        }
        
        result = self.fetcher.fetch_team_players(456)
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Player"
        mock_request.assert_called_once_with("/teams/456")


class TestDataLoader:
    """Test cases for DataLoader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DataLoader()
    
    @patch('soccer_analytics.etl.load.get_db_session')
    def test_load_competitions(self, mock_session):
        """Test loading competitions into database."""
        # Mock session and query
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        competitions_data = [
            {
                "id": 123,
                "name": "Test League",
                "code": "TL",
                "area": {"name": "Test Country", "code": "TC"},
                "currentSeason": {
                    "startDate": "2023-08-01",
                    "endDate": "2024-05-31"
                }
            }
        ]
        
        created, updated = self.loader.load_competitions(competitions_data)
        
        assert created == 1
        assert updated == 0
        mock_db_session.add.assert_called_once()
    
    @patch('soccer_analytics.etl.load.get_db_session')
    def test_load_teams(self, mock_session):
        """Test loading teams into database."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        teams_data = [
            {
                "id": 456,
                "name": "Test Team",
                "shortName": "Test",
                "tla": "TT",
                "area": {"name": "Test Country"},
                "founded": 1900
            }
        ]
        
        created, updated = self.loader.load_teams(teams_data, league_id=1)
        
        assert created == 1
        assert updated == 0
        mock_db_session.add.assert_called_once()
    
    @patch('soccer_analytics.etl.load.get_db_session')
    def test_load_players(self, mock_session):
        """Test loading players into database."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        players_data = [
            {
                "id": 789,
                "name": "Test Player",
                "firstName": "Test",
                "lastName": "Player",
                "dateOfBirth": "1990-01-01",
                "nationality": "Test Country",
                "position": "Midfielder",
                "shirtNumber": 10
            }
        ]
        
        created, updated = self.loader.load_players(players_data, team_id=1)
        
        assert created == 1
        assert updated == 0
        mock_db_session.add.assert_called_once()


def test_major_competitions_constant():
    """Test that major competitions are defined."""
    from soccer_analytics.etl.fetch import MAJOR_COMPETITIONS
    
    assert "PREMIER_LEAGUE" in MAJOR_COMPETITIONS
    assert "LA_LIGA" in MAJOR_COMPETITIONS
    assert "BUNDESLIGA" in MAJOR_COMPETITIONS
    assert "SERIE_A" in MAJOR_COMPETITIONS
    assert "LIGUE_1" in MAJOR_COMPETITIONS


def test_get_competition_id():
    """Test getting competition ID by name."""
    from soccer_analytics.etl.fetch import get_competition_id
    
    assert get_competition_id("PREMIER_LEAGUE") == 2021
    assert get_competition_id("premier_league") == 2021
    assert get_competition_id("NONEXISTENT") is None 