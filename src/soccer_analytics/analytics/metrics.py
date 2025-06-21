"""Analytics engine for calculating football metrics and statistics."""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from soccer_analytics.data_models.models import (
    League, Team, Player, Match, PlayerStats, TeamStats
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Main analytics engine for calculating football metrics."""
    
    def __init__(self, session: Session):
        """Initialize the analytics engine with a database session."""
        self.session = session
    
    def calculate_league_metrics(self, league_id: int, season_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a specific league.
        
        Args:
            league_id: Internal league ID
            season_year: Season year filter
            
        Returns:
            Dictionary containing league metrics
        """
        try:
            # Get league info
            league = self.session.query(League).filter(League.id == league_id).first()
            if not league:
                raise ValueError(f"League with ID {league_id} not found")
            
            # Base query for matches in this league
            match_query = self.session.query(Match).filter(Match.competition_id == league_id)
            
            if season_year:
                match_query = match_query.filter(
                    func.extract('year', Match.season_start_date) == season_year
                )
            
            # Get all matches
            matches = match_query.all()
            finished_matches = [m for m in matches if m.status == "FINISHED"]
            
            # Calculate basic metrics
            total_matches = len(matches)
            finished_matches_count = len(finished_matches)
            
            # Goal statistics
            total_goals = sum(
                (m.score_full_time_home or 0) + (m.score_full_time_away or 0)
                for m in finished_matches
            )
            
            avg_goals_per_match = total_goals / finished_matches_count if finished_matches_count > 0 else 0
            
            # Home vs Away statistics
            home_wins = len([m for m in finished_matches if m.score_winner == "HOME_TEAM"])
            away_wins = len([m for m in finished_matches if m.score_winner == "AWAY_TEAM"])
            draws = len([m for m in finished_matches if m.score_winner == "DRAW"])
            
            # Team count
            team_count = self.session.query(Team).filter(Team.league_id == league_id).count()
            
            # Player count
            player_count = self.session.query(Player).join(Team).filter(
                Team.league_id == league_id
            ).count()
            
            # High-scoring matches (3+ goals)
            high_scoring_matches = len([
                m for m in finished_matches 
                if (m.score_full_time_home or 0) + (m.score_full_time_away or 0) >= 3
            ])
            
            # Clean sheets percentage
            clean_sheets = len([
                m for m in finished_matches 
                if (m.score_full_time_home or 0) == 0 or (m.score_full_time_away or 0) == 0
            ])
            
            clean_sheet_percentage = clean_sheets / finished_matches_count if finished_matches_count > 0 else 0
            
            return {
                "league_name": league.name,
                "league_id": league_id,
                "season_year": season_year,
                "total_matches": total_matches,
                "finished_matches": finished_matches_count,
                "teams_count": team_count,
                "players_count": player_count,
                "total_goals": total_goals,
                "avg_goals_per_match": round(avg_goals_per_match, 2),
                "home_wins": home_wins,
                "away_wins": away_wins,
                "draws": draws,
                "home_win_percentage": round(home_wins / finished_matches_count * 100, 1) if finished_matches_count > 0 else 0,
                "away_win_percentage": round(away_wins / finished_matches_count * 100, 1) if finished_matches_count > 0 else 0,
                "draw_percentage": round(draws / finished_matches_count * 100, 1) if finished_matches_count > 0 else 0,
                "high_scoring_matches": high_scoring_matches,
                "high_scoring_percentage": round(high_scoring_matches / finished_matches_count * 100, 1) if finished_matches_count > 0 else 0,
                "clean_sheets": clean_sheets,
                "clean_sheet_percentage": round(clean_sheet_percentage * 100, 1),
            }
            
        except Exception as e:
            logger.error(f"Error calculating league metrics for league {league_id}: {e}")
            raise
    
    def calculate_team_metrics(self, team_id: int, season_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a specific team.
        
        Args:
            team_id: Internal team ID
            season_year: Season year filter
            
        Returns:
            Dictionary containing team metrics
        """
        try:
            # Get team info
            team = self.session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team with ID {team_id} not found")
            
            # Base query for team matches
            match_query = self.session.query(Match).filter(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
            )
            
            if season_year:
                match_query = match_query.filter(
                    func.extract('year', Match.season_start_date) == season_year
                )
            
            matches = match_query.all()
            finished_matches = [m for m in matches if m.status == "FINISHED"]
            
            # Calculate basic statistics
            total_matches = len(finished_matches)
            
            if total_matches == 0:
                return {
                    "team_name": team.name,
                    "team_id": team_id,
                    "season_year": season_year,
                    "matches_played": 0,
                }
            
            # Goals for and against
            goals_for = 0
            goals_against = 0
            wins = 0
            draws = 0
            losses = 0
            
            for match in finished_matches:
                if match.home_team_id == team_id:
                    # Team playing at home
                    team_goals = match.score_full_time_home or 0
                    opponent_goals = match.score_full_time_away or 0
                else:
                    # Team playing away
                    team_goals = match.score_full_time_away or 0
                    opponent_goals = match.score_full_time_home or 0
                
                goals_for += team_goals
                goals_against += opponent_goals
                
                # Determine result
                if team_goals > opponent_goals:
                    wins += 1
                elif team_goals == opponent_goals:
                    draws += 1
                else:
                    losses += 1
            
            # Calculate derived metrics
            points = wins * 3 + draws
            goal_difference = goals_for - goals_against
            win_rate = wins / total_matches
            points_per_game = points / total_matches
            goals_per_game = goals_for / total_matches
            goals_conceded_per_game = goals_against / total_matches
            
            # Clean sheets
            clean_sheets = len([
                m for m in finished_matches
                if (m.score_full_time_away == 0 and m.home_team_id == team_id) or
                   (m.score_full_time_home == 0 and m.away_team_id == team_id)
            ])
            
            return {
                "team_name": team.name,
                "team_id": team_id,
                "league_id": team.league_id,
                "season_year": season_year,
                "matches_played": total_matches,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "points": points,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_difference": goal_difference,
                "win_rate": win_rate,
                "points_per_game": points_per_game,
                "goals_per_game": goals_per_game,
                "goals_conceded_per_game": goals_conceded_per_game,
                "clean_sheets": clean_sheets,
                "clean_sheet_rate": clean_sheets / total_matches,
            }
            
        except Exception as e:
            logger.error(f"Error calculating team metrics for team {team_id}: {e}")
            raise
    
    def get_top_scorers(
        self, 
        league_id: Optional[int] = None, 
        limit: int = 10,
        season_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top goal scorers, optionally filtered by league and season.
        
        Args:
            league_id: Optional league ID filter
            limit: Number of top scorers to return
            season_year: Optional season year filter
            
        Returns:
            List of player statistics dictionaries
        """
        try:
            # Base query for player stats
            query = self.session.query(
                Player.id,
                Player.name,
                Team.name.label('team_name'),
                func.sum(PlayerStats.goals).label('total_goals'),
                func.sum(PlayerStats.assists).label('total_assists'),
                func.count(PlayerStats.id).label('matches_played'),
                func.sum(PlayerStats.minutes_played).label('total_minutes')
            ).join(PlayerStats, Player.id == PlayerStats.player_id)\
             .join(Team, Player.team_id == Team.id)
            
            if league_id:
                query = query.filter(Team.league_id == league_id)
            
            if season_year:
                query = query.join(Match, PlayerStats.match_id == Match.id)\
                             .filter(func.extract('year', Match.season_start_date) == season_year)
            
            # Group by player and order by goals
            results = query.group_by(Player.id, Player.name, Team.name)\
                          .having(func.sum(PlayerStats.goals) > 0)\
                          .order_by(func.sum(PlayerStats.goals).desc())\
                          .limit(limit)\
                          .all()
            
            return [
                {
                    "player_id": result.id,
                    "name": result.name,
                    "team_name": result.team_name,
                    "goals": result.total_goals or 0,
                    "assists": result.total_assists or 0,
                    "matches_played": result.matches_played or 0,
                    "minutes_played": result.total_minutes or 0,
                    "goals_per_game": round((result.total_goals or 0) / (result.matches_played or 1), 2),
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting top scorers: {e}")
            raise
    
    def get_league_table(
        self, 
        league_id: int, 
        season_year: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get league table/standings.
        
        Args:
            league_id: League ID
            season_year: Optional season year filter
            limit: Number of teams to return
            
        Returns:
            List of team standings
        """
        try:
            # Query team stats
            query = self.session.query(TeamStats).filter(TeamStats.league_id == league_id)
            
            if season_year:
                query = query.filter(
                    func.extract('year', TeamStats.season_start_date) == season_year
                )
            
            # Get latest season if no year specified
            if not season_year:
                latest_season = self.session.query(
                    func.max(TeamStats.season_start_date)
                ).filter(TeamStats.league_id == league_id).scalar()
                
                if latest_season:
                    query = query.filter(TeamStats.season_start_date == latest_season)
            
            team_stats = query.join(Team, TeamStats.team_id == Team.id)\
                             .order_by(TeamStats.position.asc())\
                             .limit(limit)\
                             .all()
            
            return [
                {
                    "position": stat.position,
                    "team_name": stat.team.name,
                    "team_id": stat.team_id,
                    "played_games": stat.played_games,
                    "won": stat.won,
                    "draw": stat.draw,
                    "lost": stat.lost,
                    "goals_for": stat.goals_for,
                    "goals_against": stat.goals_against,
                    "goal_difference": stat.goal_difference,
                    "points": stat.points,
                    "form": stat.form,
                }
                for stat in team_stats
            ]
            
        except Exception as e:
            logger.error(f"Error getting league table for league {league_id}: {e}")
            raise
    
    def analyze_team_performance(
        self, 
        team_id: int, 
        season_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze detailed team performance including advanced metrics.
        
        Args:
            team_id: Team ID
            season_year: Optional season year filter
            
        Returns:
            Detailed performance analysis
        """
        try:
            # Get basic team metrics
            basic_metrics = self.calculate_team_metrics(team_id, season_year)
            
            # Get additional performance metrics
            team_query = self.session.query(Match).filter(
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                Match.status == "FINISHED"
            )
            
            if season_year:
                team_query = team_query.filter(
                    func.extract('year', Match.season_start_date) == season_year
                )
            
            matches = team_query.all()
            
            # Form analysis (last 5 matches)
            recent_matches = sorted(matches, key=lambda x: x.utc_date, reverse=True)[:5]
            form_results = []
            
            for match in recent_matches:
                if match.home_team_id == team_id:
                    team_goals = match.score_full_time_home or 0
                    opponent_goals = match.score_full_time_away or 0
                else:
                    team_goals = match.score_full_time_away or 0
                    opponent_goals = match.score_full_time_home or 0
                
                if team_goals > opponent_goals:
                    form_results.append('W')
                elif team_goals == opponent_goals:
                    form_results.append('D')
                else:
                    form_results.append('L')
            
            # Home vs Away performance
            home_matches = [m for m in matches if m.home_team_id == team_id]
            away_matches = [m for m in matches if m.away_team_id == team_id]
            
            home_performance = self._analyze_home_away_performance(home_matches, True)
            away_performance = self._analyze_home_away_performance(away_matches, False)
            
            # Combine all metrics
            performance = {
                **basic_metrics,
                "form": "".join(form_results),
                "recent_matches_count": len(recent_matches),
                "home_performance": home_performance,
                "away_performance": away_performance,
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error analyzing team performance for team {team_id}: {e}")
            raise
    
    def _analyze_home_away_performance(self, matches: List[Match], is_home: bool) -> Dict[str, Any]:
        """Analyze home or away performance for a team."""
        if not matches:
            return {"matches": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
        
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for match in matches:
            if is_home:
                team_goals = match.score_full_time_home or 0
                opponent_goals = match.score_full_time_away or 0
            else:
                team_goals = match.score_full_time_away or 0
                opponent_goals = match.score_full_time_home or 0
            
            goals_for += team_goals
            goals_against += opponent_goals
            
            if team_goals > opponent_goals:
                wins += 1
            elif team_goals == opponent_goals:
                draws += 1
            else:
                losses += 1
        
        total_matches = len(matches)
        return {
            "matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "win_rate": wins / total_matches if total_matches > 0 else 0,
            "points": wins * 3 + draws,
            "points_per_game": (wins * 3 + draws) / total_matches if total_matches > 0 else 0,
        }
    
    def get_player_stats(
        self, 
        player_id: int, 
        season_year: Optional[int] = None,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive player statistics.
        
        Args:
            player_id: Player ID
            season_year: Optional season year filter
            detailed: Include detailed statistics
            
        Returns:
            Player statistics dictionary
        """
        try:
            # Get player info
            player = self.session.query(Player).filter(Player.id == player_id).first()
            if not player:
                raise ValueError(f"Player with ID {player_id} not found")
            
            # Base query for player stats
            stats_query = self.session.query(PlayerStats).filter(PlayerStats.player_id == player_id)
            
            if season_year:
                stats_query = stats_query.join(Match, PlayerStats.match_id == Match.id)\
                                       .filter(func.extract('year', Match.season_start_date) == season_year)
            
            player_stats = stats_query.all()
            
            if not player_stats:
                return {
                    "player_id": player_id,
                    "name": player.name,
                    "position": player.position,
                    "team_name": player.team.name if player.team else "No Team",
                    "nationality": player.nationality,
                    "matches_played": 0,
                }
            
            # Calculate aggregated stats
            total_stats = {
                "matches_played": len(player_stats),
                "minutes_played": sum(stat.minutes_played for stat in player_stats),
                "goals": sum(stat.goals for stat in player_stats),
                "assists": sum(stat.assists for stat in player_stats),
                "yellow_cards": sum(stat.yellow_cards for stat in player_stats),
                "red_cards": sum(stat.red_cards for stat in player_stats),
            }
            
            # Calculate age if date of birth is available
            age = None
            if player.date_of_birth:
                today = date.today()
                age = today.year - player.date_of_birth.year - (
                    (today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day)
                )
            
            result = {
                "player_id": player_id,
                "name": player.name,
                "position": player.position,
                "team_name": player.team.name if player.team else "No Team",
                "nationality": player.nationality,
                "age": age,
                "season_year": season_year,
                **total_stats,
                "goals_per_game": round(total_stats["goals"] / total_stats["matches_played"], 2) if total_stats["matches_played"] > 0 else 0,
                "assists_per_game": round(total_stats["assists"] / total_stats["matches_played"], 2) if total_stats["matches_played"] > 0 else 0,
                "minutes_per_game": round(total_stats["minutes_played"] / total_stats["matches_played"], 1) if total_stats["matches_played"] > 0 else 0,
            }
            
            if detailed:
                # Add detailed statistics
                detailed_stats = {
                    "shots_total": sum(stat.shots_total for stat in player_stats),
                    "shots_on_target": sum(stat.shots_on_target for stat in player_stats),
                    "passes_total": sum(stat.passes_total for stat in player_stats),
                    "passes_completed": sum(stat.passes_completed for stat in player_stats),
                    "tackles": sum(stat.tackles for stat in player_stats),
                    "interceptions": sum(stat.interceptions for stat in player_stats),
                    "fouls_committed": sum(stat.fouls_committed for stat in player_stats),
                    "fouls_drawn": sum(stat.fouls_drawn for stat in player_stats),
                }
                
                # Calculate percentages
                if detailed_stats["shots_total"] > 0:
                    detailed_stats["shot_accuracy"] = detailed_stats["shots_on_target"] / detailed_stats["shots_total"]
                else:
                    detailed_stats["shot_accuracy"] = 0
                
                if detailed_stats["passes_total"] > 0:
                    detailed_stats["pass_accuracy"] = detailed_stats["passes_completed"] / detailed_stats["passes_total"]
                else:
                    detailed_stats["pass_accuracy"] = 0
                
                result["detailed_stats"] = detailed_stats
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting player stats for player {player_id}: {e}")
            raise
    
    def calculate_all_league_metrics(self, season_year: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate metrics for all leagues.
        
        Args:
            season_year: Optional season year filter
            
        Returns:
            Dictionary mapping league names to their metrics
        """
        try:
            leagues = self.session.query(League).all()
            all_metrics = {}
            
            for league in leagues:
                try:
                    metrics = self.calculate_league_metrics(league.id, season_year)
                    all_metrics[league.name] = metrics
                except Exception as e:
                    logger.warning(f"Failed to calculate metrics for league {league.name}: {e}")
                    continue
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Error calculating all league metrics: {e}")
            raise
    
    def get_league_averages(self, league_id: int, season_year: Optional[int] = None) -> Dict[str, float]:
        """
        Get league average statistics for comparison.
        
        Args:
            league_id: League ID
            season_year: Optional season year filter
            
        Returns:
            Dictionary of league averages
        """
        try:
            # Get all teams in the league
            teams = self.session.query(Team).filter(Team.league_id == league_id).all()
            
            if not teams:
                return {}
            
            # Calculate metrics for each team
            team_metrics = []
            for team in teams:
                try:
                    metrics = self.calculate_team_metrics(team.id, season_year)
                    if metrics.get("matches_played", 0) > 0:
                        team_metrics.append(metrics)
                except Exception as e:
                    logger.warning(f"Failed to calculate metrics for team {team.name}: {e}")
                    continue
            
            if not team_metrics:
                return {}
            
            # Calculate averages
            averages = {}
            numeric_fields = [
                "points_per_game", "goals_per_game", "goals_conceded_per_game", 
                "win_rate", "clean_sheet_rate"
            ]
            
            for field in numeric_fields:
                values = [metrics.get(field, 0) for metrics in team_metrics]
                averages[field] = sum(values) / len(values) if values else 0
            
            return averages
            
        except Exception as e:
            logger.error(f"Error calculating league averages for league {league_id}: {e}")
            raise