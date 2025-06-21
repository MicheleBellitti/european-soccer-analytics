"""Integration tests for database functionality."""

import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from soccer_analytics.config.database import Base, create_test_engine
from soccer_analytics.data_models.models import (
    League, Team, Player, Match, PlayerStats, TeamStats
)


@pytest.fixture(scope="function")
def test_db():
    """Create test database fixture."""
    engine = create_test_engine("sqlite:///:memory:")
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestSessionLocal()
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_league(test_db):
    """Test creating a league."""
    league = League(
        external_id=123,
        name="Test League",
        code="TL",
        area_name="Test Country",
        area_code="TC",
        current_season_start=date(2023, 8, 1),
        current_season_end=date(2024, 5, 31)
    )
    
    test_db.add(league)
    test_db.commit()
    
    # Query back
    saved_league = test_db.query(League).filter(League.external_id == 123).first()
    assert saved_league is not None
    assert saved_league.name == "Test League"
    assert saved_league.code == "TL"


def test_create_team(test_db):
    """Test creating a team."""
    # Create league first
    league = League(
        external_id=123,
        name="Test League",
        code="TL",
        area_name="Test Country"
    )
    test_db.add(league)
    test_db.commit()
    
    # Create team
    team = Team(
        external_id=456,
        name="Test Team",
        short_name="Test",
        tla="TT",
        area_name="Test Country",
        founded=1900,
        league_id=league.id
    )
    
    test_db.add(team)
    test_db.commit()
    
    # Query back
    saved_team = test_db.query(Team).filter(Team.external_id == 456).first()
    assert saved_team is not None
    assert saved_team.name == "Test Team"
    assert saved_team.league_id == league.id


def test_create_player(test_db):
    """Test creating a player."""
    # Create league and team first
    league = League(external_id=123, name="Test League", area_name="Test Country")
    test_db.add(league)
    test_db.commit()
    
    team = Team(
        external_id=456,
        name="Test Team",
        area_name="Test Country",
        league_id=league.id
    )
    test_db.add(team)
    test_db.commit()
    
    # Create player
    player = Player(
        external_id=789,
        name="Test Player",
        first_name="Test",
        last_name="Player",
        date_of_birth=date(1990, 1, 1),
        nationality="Test Country",
        position="Midfielder",
        shirt_number=10,
        team_id=team.id
    )
    
    test_db.add(player)
    test_db.commit()
    
    # Query back
    saved_player = test_db.query(Player).filter(Player.external_id == 789).first()
    assert saved_player is not None
    assert saved_player.name == "Test Player"
    assert saved_player.team_id == team.id


def test_create_match(test_db):
    """Test creating a match."""
    # Create league and teams first
    league = League(external_id=123, name="Test League", area_name="Test Country")
    test_db.add(league)
    test_db.commit()
    
    home_team = Team(
        external_id=456,
        name="Home Team",
        area_name="Test Country",
        league_id=league.id
    )
    away_team = Team(
        external_id=457,
        name="Away Team",
        area_name="Test Country",
        league_id=league.id
    )
    test_db.add_all([home_team, away_team])
    test_db.commit()
    
    # Create match
    match = Match(
        external_id=999,
        utc_date=datetime(2023, 12, 1, 15, 0),
        status="FINISHED",
        matchday=10,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        competition_id=league.id,
        score_full_time_home=2,
        score_full_time_away=1,
        score_winner="HOME_TEAM"
    )
    
    test_db.add(match)
    test_db.commit()
    
    # Query back
    saved_match = test_db.query(Match).filter(Match.external_id == 999).first()
    assert saved_match is not None
    assert saved_match.home_team_id == home_team.id
    assert saved_match.away_team_id == away_team.id
    assert saved_match.score_full_time_home == 2
    assert saved_match.score_full_time_away == 1


def test_relationships(test_db):
    """Test model relationships."""
    # Create complete hierarchy
    league = League(external_id=123, name="Test League", area_name="Test Country")
    test_db.add(league)
    test_db.commit()
    
    team = Team(
        external_id=456,
        name="Test Team",
        area_name="Test Country",
        league_id=league.id
    )
    test_db.add(team)
    test_db.commit()
    
    player = Player(
        external_id=789,
        name="Test Player",
        nationality="Test Country",
        position="Midfielder",
        team_id=team.id
    )
    test_db.add(player)
    test_db.commit()
    
    # Test relationships
    assert league.teams[0] == team
    assert team.league == league
    assert team.players[0] == player
    assert player.team == team


def test_team_stats(test_db):
    """Test team statistics functionality."""
    # Create league and team
    league = League(external_id=123, name="Test League", area_name="Test Country")
    test_db.add(league)
    test_db.commit()
    
    team = Team(
        external_id=456,
        name="Test Team",
        area_name="Test Country",
        league_id=league.id
    )
    test_db.add(team)
    test_db.commit()
    
    # Create team stats
    team_stats = TeamStats(
        team_id=team.id,
        league_id=league.id,
        season_start_date=date(2023, 8, 1),
        season_end_date=date(2024, 5, 31),
        position=1,
        played_games=10,
        won=8,
        draw=1,
        lost=1,
        points=25,
        goals_for=20,
        goals_against=5,
        goal_difference=15
    )
    
    test_db.add(team_stats)
    test_db.commit()
    
    # Query back
    saved_stats = test_db.query(TeamStats).filter(TeamStats.team_id == team.id).first()
    assert saved_stats is not None
    assert saved_stats.position == 1
    assert saved_stats.points == 25
    assert saved_stats.goal_difference == 15 