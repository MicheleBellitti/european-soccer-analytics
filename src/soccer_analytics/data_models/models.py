"""SQLAlchemy ORM models for the European Soccer Analytics platform."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from soccer_analytics.config.database import Base


class League(Base):
    """Model for football leagues/competitions."""
    
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, index=True)
    area_name = Column(String(100), nullable=False)  # Country/Region
    area_code = Column(String(3))  # Country code
    current_season_start = Column(Date)
    current_season_end = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="competition")
    
    def __repr__(self) -> str:
        try:
            return f"<League(id={self.id}, external_id={self.external_id})>"
        except:
            return f"<League(external_id={getattr(self, 'external_id', 'Unknown')})>"


class Team(Base):
    """Model for football teams/clubs."""
    
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    short_name = Column(String(100))
    tla = Column(String(5))  # Three Letter Abbreviation
    crest = Column(String(500))  # URL to team crest/logo
    area_name = Column(String(100))  # Country
    area_code = Column(String(3))
    address = Column(Text)
    website = Column(String(500))
    email = Column(String(255))
    phone = Column(String(50))
    founded = Column(Integer)  # Year founded
    club_colors = Column(String(255))
    venue = Column(String(255))
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    league = relationship("League", back_populates="teams")
    players = relationship("Player", back_populates="team")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    team_stats = relationship("TeamStats", back_populates="team")
    
    def __repr__(self) -> str:
        try:
            return f"<Team(id={self.id}, external_id={self.external_id})>"
        except:
            return f"<Team(external_id={getattr(self, 'external_id', 'Unknown')})>"


class Player(Base):
    """Model for football players."""
    
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    nationality = Column(String(100))
    position = Column(String(50))  # GOALKEEPER, DEFENCE, MIDFIELD, OFFENCE
    shirt_number = Column(Integer)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # Can be null if player is without team
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="players")
    player_stats = relationship("PlayerStats", back_populates="player")
    
    def __repr__(self) -> str:
        try:
            return f"<Player(id={self.id}, external_id={self.external_id})>"
        except:
            return f"<Player(external_id={getattr(self, 'external_id', 'Unknown')})>"


class Match(Base):
    """Model for football matches."""
    
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    utc_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False)  # SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED, POSTPONED, SUSPENDED, CANCELLED
    matchday = Column(Integer)  # Matchday/round number
    stage = Column(String(50))  # REGULAR_SEASON, PLAYOFFS, etc.
    group = Column(String(10))  # For group stages
    last_updated = Column(DateTime(timezone=True))
    
    # Teams
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Scores
    score_winner = Column(String(10))  # HOME_TEAM, AWAY_TEAM, DRAW
    score_duration = Column(String(20))  # REGULAR, EXTRA_TIME, PENALTY_SHOOTOUT
    score_full_time_home = Column(Integer)
    score_full_time_away = Column(Integer)
    score_half_time_home = Column(Integer)
    score_half_time_away = Column(Integer)
    
    # Competition
    competition_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season_start_date = Column(Date)
    season_end_date = Column(Date)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    competition = relationship("League", back_populates="matches")
    player_stats = relationship("PlayerStats", back_populates="match")
    
    def __repr__(self) -> str:
        try:
            return f"<Match(id={self.id}, external_id={self.external_id})>"
        except:
            return f"<Match(external_id={getattr(self, 'external_id', 'Unknown')})>"


class PlayerStats(Base):
    """Model for player statistics in specific matches."""
    
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    # Basic stats
    minutes_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    
    # Extended stats (when available)
    shots_total = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    passes_total = Column(Integer, default=0)
    passes_completed = Column(Integer, default=0)
    pass_accuracy = Column(Float)  # Percentage
    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    fouls_drawn = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="player_stats")
    match = relationship("Match", back_populates="player_stats")
    
    def __repr__(self) -> str:
        try:
            return f"<PlayerStats(id={self.id}, player_id={self.player_id}, match_id={self.match_id})>"
        except:
            return f"<PlayerStats(id={getattr(self, 'id', 'Unknown')})>"


class TeamStats(Base):
    """Model for team statistics aggregated by season/competition."""
    
    __tablename__ = "team_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season_start_date = Column(Date, nullable=False)
    season_end_date = Column(Date, nullable=False)
    
    # League table stats
    position = Column(Integer)
    played_games = Column(Integer, default=0)
    form = Column(String(10))  # Last 5 games: W, D, L
    won = Column(Integer, default=0)
    draw = Column(Integer, default=0)
    lost = Column(Integer, default=0)
    points = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="team_stats")
    league = relationship("League")
    
    def __repr__(self) -> str:
        try:
            return f"<TeamStats(id={self.id}, team_id={self.team_id}, league_id={self.league_id})>"
        except:
            return f"<TeamStats(id={getattr(self, 'id', 'Unknown')})>"