"""Data loading module for European Soccer Analytics platform."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from soccer_analytics.config.database import get_db_session
from soccer_analytics.data_models.models import (
    League, Team, Player, Match, PlayerStats, TeamStats
)

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads data from API responses into the database."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.session: Optional[Session] = None
    
    def load_competitions(self, competitions_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Load competitions/leagues into the database.
        
        Args:
            competitions_data: List of competition data from API
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        with get_db_session() as session:
            for comp_data in competitions_data:
                try:
                    # Check if league already exists
                    existing_league = session.query(League).filter(
                        League.external_id == comp_data["id"]
                    ).first()
                    
                    if existing_league:
                        # Update existing league
                        existing_league.name = comp_data.get("name", existing_league.name)
                        existing_league.code = comp_data.get("code", existing_league.code)
                        existing_league.area_name = comp_data.get("area", {}).get("name", existing_league.area_name)
                        existing_league.area_code = comp_data.get("area", {}).get("code", existing_league.area_code)
                        
                        # Update season dates if available
                        if "currentSeason" in comp_data:
                            season = comp_data["currentSeason"]
                            if "startDate" in season:
                                existing_league.current_season_start = datetime.strptime(
                                    season["startDate"], "%Y-%m-%d"
                                ).date()
                            if "endDate" in season:
                                existing_league.current_season_end = datetime.strptime(
                                    season["endDate"], "%Y-%m-%d"
                                ).date()
                        
                        updated_count += 1
                        logger.debug(f"Updated league: {existing_league.name}")
                    
                    else:
                        # Create new league
                        league = League(
                            external_id=comp_data["id"],
                            name=comp_data.get("name", "Unknown"),
                            code=comp_data.get("code"),
                            area_name=comp_data.get("area", {}).get("name", "Unknown"),
                            area_code=comp_data.get("area", {}).get("code")
                        )
                        
                        # Set season dates if available
                        if "currentSeason" in comp_data:
                            season = comp_data["currentSeason"]
                            if "startDate" in season:
                                league.current_season_start = datetime.strptime(
                                    season["startDate"], "%Y-%m-%d"
                                ).date()
                            if "endDate" in season:
                                league.current_season_end = datetime.strptime(
                                    season["endDate"], "%Y-%m-%d"
                                ).date()
                        
                        session.add(league)
                        created_count += 1
                        logger.debug(f"Created league: {league.name}")
                
                except Exception as e:
                    logger.error(f"Error loading competition {comp_data.get('name', 'Unknown')}: {e}")
                    continue
        
        logger.info(f"Loaded competitions: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def load_teams(self, teams_data: List[Dict[str, Any]], league_id: int) -> Tuple[int, int]:
        """
        Load teams into the database.
        
        Args:
            teams_data: List of team data from API
            league_id: Database ID of the league these teams belong to
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        with get_db_session() as session:
            for team_data in teams_data:
                try:
                    # Check if team already exists
                    existing_team = session.query(Team).filter(
                        Team.external_id == team_data["id"]
                    ).first()
                    
                    if existing_team:
                        # Update existing team
                        existing_team.name = team_data.get("name", existing_team.name)
                        existing_team.short_name = team_data.get("shortName", existing_team.short_name)
                        existing_team.tla = team_data.get("tla", existing_team.tla)
                        existing_team.crest = team_data.get("crest", existing_team.crest)
                        existing_team.area_name = team_data.get("area", {}).get("name", existing_team.area_name)
                        existing_team.area_code = team_data.get("area", {}).get("code", existing_team.area_code)
                        existing_team.address = team_data.get("address", existing_team.address)
                        existing_team.website = team_data.get("website", existing_team.website)
                        existing_team.email = team_data.get("email", existing_team.email)
                        existing_team.phone = team_data.get("phone", existing_team.phone)
                        existing_team.founded = team_data.get("founded", existing_team.founded)
                        existing_team.club_colors = team_data.get("clubColors", existing_team.club_colors)
                        existing_team.venue = team_data.get("venue", existing_team.venue)
                        existing_team.league_id = league_id
                        
                        updated_count += 1
                        logger.debug(f"Updated team: {existing_team.name}")
                    
                    else:
                        # Create new team
                        team = Team(
                            external_id=team_data["id"],
                            name=team_data.get("name", "Unknown"),
                            short_name=team_data.get("shortName"),
                            tla=team_data.get("tla"),
                            crest=team_data.get("crest"),
                            area_name=team_data.get("area", {}).get("name"),
                            area_code=team_data.get("area", {}).get("code"),
                            address=team_data.get("address"),
                            website=team_data.get("website"),
                            email=team_data.get("email"),
                            phone=team_data.get("phone"),
                            founded=team_data.get("founded"),
                            club_colors=team_data.get("clubColors"),
                            venue=team_data.get("venue"),
                            league_id=league_id
                        )
                        
                        session.add(team)
                        created_count += 1
                        logger.debug(f"Created team: {team.name}")
                
                except Exception as e:
                    logger.error(f"Error loading team {team_data.get('name', 'Unknown')}: {e}")
                    continue
        
        logger.info(f"Loaded teams: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def load_players(self, players_data: List[Dict[str, Any]], team_id: int) -> Tuple[int, int]:
        """
        Load players into the database.
        
        Args:
            players_data: List of player data from API
            team_id: Database ID of the team these players belong to
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        with get_db_session() as session:
            for player_data in players_data:
                try:
                    # Check if player already exists
                    existing_player = session.query(Player).filter(
                        Player.external_id == player_data["id"]
                    ).first()
                    
                    date_of_birth = None
                    if player_data.get("dateOfBirth"):
                        try:
                            date_of_birth = datetime.strptime(
                                player_data["dateOfBirth"], "%Y-%m-%d"
                            ).date()
                        except ValueError:
                            logger.warning(f"Invalid date format for player {player_data.get('name')}: {player_data.get('dateOfBirth')}")
                    
                    if existing_player:
                        # Update existing player
                        existing_player.name = player_data.get("name", existing_player.name)
                        existing_player.first_name = player_data.get("firstName", existing_player.first_name)
                        existing_player.last_name = player_data.get("lastName", existing_player.last_name)
                        existing_player.date_of_birth = date_of_birth or existing_player.date_of_birth
                        existing_player.nationality = player_data.get("nationality", existing_player.nationality)
                        existing_player.position = player_data.get("position", existing_player.position)
                        existing_player.shirt_number = player_data.get("shirtNumber", existing_player.shirt_number)
                        existing_player.team_id = team_id
                        
                        updated_count += 1
                        logger.debug(f"Updated player: {existing_player.name}")
                    
                    else:
                        # Create new player
                        player = Player(
                            external_id=player_data["id"],
                            name=player_data.get("name", "Unknown"),
                            first_name=player_data.get("firstName"),
                            last_name=player_data.get("lastName"),
                            date_of_birth=date_of_birth,
                            nationality=player_data.get("nationality"),
                            position=player_data.get("position"),
                            shirt_number=player_data.get("shirtNumber"),
                            team_id=team_id
                        )
                        
                        session.add(player)
                        created_count += 1
                        logger.debug(f"Created player: {player.name}")
                
                except Exception as e:
                    logger.error(f"Error loading player {player_data.get('name', 'Unknown')}: {e}")
                    continue
        
        logger.info(f"Loaded players: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def load_matches(self, matches_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Load matches into the database.
        
        Args:
            matches_data: List of match data from API
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        with get_db_session() as session:
            for match_data in matches_data:
                try:
                    # Get team IDs from database
                    home_team = session.query(Team).filter(
                        Team.external_id == match_data["homeTeam"]["id"]
                    ).first()
                    away_team = session.query(Team).filter(
                        Team.external_id == match_data["awayTeam"]["id"]
                    ).first()
                    competition = session.query(League).filter(
                        League.external_id == match_data["competition"]["id"]
                    ).first()
                    
                    if not home_team or not away_team or not competition:
                        logger.warning(f"Missing team or competition data for match {match_data['id']}")
                        continue
                    
                    # Parse UTC date
                    utc_date = datetime.fromisoformat(
                        match_data["utcDate"].replace("Z", "+00:00")
                    )
                    
                    # Parse season dates if available
                    season_start = None
                    season_end = None
                    if "season" in match_data:
                        season = match_data["season"]
                        if "startDate" in season:
                            season_start = datetime.strptime(season["startDate"], "%Y-%m-%d").date()
                        if "endDate" in season:
                            season_end = datetime.strptime(season["endDate"], "%Y-%m-%d").date()
                    
                    # Check if match already exists
                    existing_match = session.query(Match).filter(
                        Match.external_id == match_data["id"]
                    ).first()
                    
                    # Parse scores
                    score_data = match_data.get("score", {})
                    full_time = score_data.get("fullTime", {})
                    half_time = score_data.get("halfTime", {})
                    
                    if existing_match:
                        # Update existing match
                        existing_match.utc_date = utc_date
                        existing_match.status = match_data.get("status", existing_match.status)
                        existing_match.matchday = match_data.get("matchday", existing_match.matchday)
                        existing_match.stage = match_data.get("stage", existing_match.stage)
                        existing_match.group = match_data.get("group", existing_match.group)
                        
                        if match_data.get("lastUpdated"):
                            existing_match.last_updated = datetime.fromisoformat(
                                match_data["lastUpdated"].replace("Z", "+00:00")
                            )
                        
                        # Update scores
                        existing_match.score_winner = score_data.get("winner", existing_match.score_winner)
                        existing_match.score_duration = score_data.get("duration", existing_match.score_duration)
                        existing_match.score_full_time_home = full_time.get("home", existing_match.score_full_time_home)
                        existing_match.score_full_time_away = full_time.get("away", existing_match.score_full_time_away)
                        existing_match.score_half_time_home = half_time.get("home", existing_match.score_half_time_home)
                        existing_match.score_half_time_away = half_time.get("away", existing_match.score_half_time_away)
                        
                        updated_count += 1
                        logger.debug(f"Updated match: {home_team.name} vs {away_team.name}")
                    
                    else:
                        # Create new match
                        match = Match(
                            external_id=match_data["id"],
                            utc_date=utc_date,
                            status=match_data.get("status", "SCHEDULED"),
                            matchday=match_data.get("matchday"),
                            stage=match_data.get("stage"),
                            group=match_data.get("group"),
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            competition_id=competition.id,
                            season_start_date=season_start,
                            season_end_date=season_end,
                            score_winner=score_data.get("winner"),
                            score_duration=score_data.get("duration"),
                            score_full_time_home=full_time.get("home"),
                            score_full_time_away=full_time.get("away"),
                            score_half_time_home=half_time.get("home"),
                            score_half_time_away=half_time.get("away")
                        )
                        
                        if match_data.get("lastUpdated"):
                            match.last_updated = datetime.fromisoformat(
                                match_data["lastUpdated"].replace("Z", "+00:00")
                            )
                        
                        session.add(match)
                        created_count += 1
                        logger.debug(f"Created match: {home_team.name} vs {away_team.name}")
                
                except Exception as e:
                    logger.error(f"Error loading match {match_data.get('id', 'Unknown')}: {e}")
                    continue
        
        logger.info(f"Loaded matches: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def load_standings(self, standings_data: Dict[str, Any]) -> Tuple[int, int]:
        """
        Load team standings/stats into the database.
        
        Args:
            standings_data: Standings data from API
            
        Returns:
            Tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        if "standings" not in standings_data:
            logger.warning("No standings data found")
            return created_count, updated_count
        
        with get_db_session() as session:
            # Get competition
            competition = session.query(League).filter(
                League.external_id == standings_data["competition"]["id"]
            ).first()
            
            if not competition:
                logger.warning(f"Competition not found: {standings_data['competition']['id']}")
                return created_count, updated_count
            
            # Parse season dates
            season_data = standings_data.get("season", {})
            season_start = None
            season_end = None
            
            if "startDate" in season_data:
                season_start = datetime.strptime(season_data["startDate"], "%Y-%m-%d").date()
            if "endDate" in season_data:
                season_end = datetime.strptime(season_data["endDate"], "%Y-%m-%d").date()
            
            # Process each standing table (usually just one for league tables)
            for standing_table in standings_data["standings"]:
                for team_standing in standing_table.get("table", []):
                    try:
                        # Get team from database
                        team = session.query(Team).filter(
                            Team.external_id == team_standing["team"]["id"]
                        ).first()
                        
                        if not team:
                            logger.warning(f"Team not found: {team_standing['team']['id']}")
                            continue
                        
                        # Check if team stats already exist for this season
                        existing_stats = session.query(TeamStats).filter(
                            TeamStats.team_id == team.id,
                            TeamStats.league_id == competition.id,
                            TeamStats.season_start_date == season_start
                        ).first()
                        
                        if existing_stats:
                            # Update existing stats
                            existing_stats.position = team_standing.get("position", existing_stats.position)
                            existing_stats.played_games = team_standing.get("playedGames", existing_stats.played_games)
                            existing_stats.form = team_standing.get("form", existing_stats.form)
                            existing_stats.won = team_standing.get("won", existing_stats.won)
                            existing_stats.draw = team_standing.get("draw", existing_stats.draw)
                            existing_stats.lost = team_standing.get("lost", existing_stats.lost)
                            existing_stats.points = team_standing.get("points", existing_stats.points)
                            existing_stats.goals_for = team_standing.get("goalsFor", existing_stats.goals_for)
                            existing_stats.goals_against = team_standing.get("goalsAgainst", existing_stats.goals_against)
                            existing_stats.goal_difference = team_standing.get("goalDifference", existing_stats.goal_difference)
                            
                            updated_count += 1
                            logger.debug(f"Updated team stats: {team.name}")
                        
                        else:
                            # Create new team stats
                            team_stats = TeamStats(
                                team_id=team.id,
                                league_id=competition.id,
                                season_start_date=season_start,
                                season_end_date=season_end,
                                position=team_standing.get("position"),
                                played_games=team_standing.get("playedGames", 0),
                                form=team_standing.get("form"),
                                won=team_standing.get("won", 0),
                                draw=team_standing.get("draw", 0),
                                lost=team_standing.get("lost", 0),
                                points=team_standing.get("points", 0),
                                goals_for=team_standing.get("goalsFor", 0),
                                goals_against=team_standing.get("goalsAgainst", 0),
                                goal_difference=team_standing.get("goalDifference", 0)
                            )
                            
                            session.add(team_stats)
                            created_count += 1
                            logger.debug(f"Created team stats: {team.name}")
                    
                    except Exception as e:
                        logger.error(f"Error loading team standings for {team_standing.get('team', {}).get('name', 'Unknown')}: {e}")
                        continue
        
        logger.info(f"Loaded team standings: {created_count} created, {updated_count} updated")
        return created_count, updated_count


def get_league_by_external_id(external_id: int) -> Optional[int]:
    """
    Get league internal ID by external API ID.
    
    Args:
        external_id: External API ID
        
    Returns:
        League internal ID if found, None otherwise
    """
    with get_db_session() as session:
        league = session.query(League).filter(League.external_id == external_id).first()
        return league.id if league else None


def get_team_by_external_id(external_id: int) -> Optional[int]:
    """
    Get team internal ID by external API ID.
    
    Args:
        external_id: External API ID
        
    Returns:
        Team internal ID if found, None otherwise
    """
    with get_db_session() as session:
        team = session.query(Team).filter(Team.external_id == external_id).first()
        return team.id if team else None 