"""Advanced calculations and statistical analysis for football data."""

import logging
import math
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from soccer_analytics.data_models.models import (
    League, Team, Player, Match, PlayerStats, TeamStats
)

logger = logging.getLogger(__name__)


class AdvancedMetrics:
    """Class for calculating advanced football metrics and statistics."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    def calculate_expected_goals(self, team_id: int, season_year: Optional[int] = None) -> Dict[str, float]:
        """
        Calculate Expected Goals (xG) estimation based on shot data.
        Note: This is a simplified xG model for demonstration.
        
        Args:
            team_id: Team ID
            season_year: Season year filter
            
        Returns:
            Dictionary with xG metrics
        """
        try:
            # Get all player stats for the team
            query = self.session.query(PlayerStats).join(Player).filter(
                Player.team_id == team_id
            )
            
            if season_year:
                query = query.join(Match, PlayerStats.match_id == Match.id)\
                             .filter(func.extract('year', Match.season_start_date) == season_year)
            
            player_stats = query.all()
            
            if not player_stats:
                return {"xg_for": 0.0, "xg_against": 0.0, "xg_difference": 0.0}
            
            # Simplified xG calculation based on shots on target
            # In a real implementation, this would use shot location, type, etc.
            total_shots_on_target = sum(stat.shots_on_target for stat in player_stats)
            total_shots = sum(stat.shots_total for stat in player_stats)
            
            # Basic xG estimation: shots on target * average conversion rate
            conversion_rate = 0.35  # Average conversion rate for shots on target
            xg_for = total_shots_on_target * conversion_rate
            
            # For xG against, we'd need opponent data - simplified here
            actual_goals = sum(stat.goals for stat in player_stats)
            xg_against = actual_goals * 0.9  # Simplified estimation
            
            return {
                "xg_for": round(xg_for, 2),
                "xg_against": round(xg_against, 2),
                "xg_difference": round(xg_for - xg_against, 2),
                "shots_total": total_shots,
                "shots_on_target": total_shots_on_target,
                "conversion_rate": round(actual_goals / total_shots_on_target if total_shots_on_target > 0 else 0, 3)
            }
            
        except Exception as e:
            logger.error(f"Error calculating xG for team {team_id}: {e}")
            raise
    
    def calculate_possession_metrics(self, team_id: int, season_year: Optional[int] = None) -> Dict[str, float]:
        """
        Calculate possession-based metrics.
        
        Args:
            team_id: Team ID
            season_year: Season year filter
            
        Returns:
            Dictionary with possession metrics
        """
        try:
            # Get player pass statistics
            query = self.session.query(PlayerStats).join(Player).filter(
                Player.team_id == team_id
            )
            
            if season_year:
                query = query.join(Match, PlayerStats.match_id == Match.id)\
                             .filter(func.extract('year', Match.season_start_date) == season_year)
            
            player_stats = query.all()
            
            if not player_stats:
                return {
                    "total_passes": 0,
                    "completed_passes": 0,
                    "pass_accuracy": 0.0,
                    "passes_per_game": 0.0
                }
            
            total_passes = sum(stat.passes_total for stat in player_stats)
            completed_passes = sum(stat.passes_completed for stat in player_stats)
            
            # Calculate matches played
            matches_played = len(set(stat.match_id for stat in player_stats))
            
            pass_accuracy = completed_passes / total_passes if total_passes > 0 else 0
            passes_per_game = total_passes / matches_played if matches_played > 0 else 0
            
            return {
                "total_passes": total_passes,
                "completed_passes": completed_passes,
                "pass_accuracy": round(pass_accuracy, 3),
                "passes_per_game": round(passes_per_game, 1),
                "matches_played": matches_played
            }
            
        except Exception as e:
            logger.error(f"Error calculating possession metrics for team {team_id}: {e}")
            raise
    
    def calculate_defensive_metrics(self, team_id: int, season_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate defensive performance metrics.
        
        Args:
            team_id: Team ID
            season_year: Season year filter
            
        Returns:
            Dictionary with defensive metrics
        """
        try:
            # Get player defensive stats
            query = self.session.query(PlayerStats).join(Player).filter(
                Player.team_id == team_id
            )
            
            if season_year:
                query = query.join(Match, PlayerStats.match_id == Match.id)\
                             .filter(func.extract('year', Match.season_start_date) == season_year)
            
            player_stats = query.all()
            
            if not player_stats:
                return {}
            
            total_tackles = sum(stat.tackles for stat in player_stats)
            total_interceptions = sum(stat.interceptions for stat in player_stats)
            total_fouls = sum(stat.fouls_committed for stat in player_stats)
            
            matches_played = len(set(stat.match_id for stat in player_stats))
            
            return {
                "total_tackles": total_tackles,
                "total_interceptions": total_interceptions,
                "total_fouls_committed": total_fouls,
                "tackles_per_game": round(total_tackles / matches_played if matches_played > 0 else 0, 1),
                "interceptions_per_game": round(total_interceptions / matches_played if matches_played > 0 else 0, 1),
                "fouls_per_game": round(total_fouls / matches_played if matches_played > 0 else 0, 1),
                "defensive_actions_per_game": round((total_tackles + total_interceptions) / matches_played if matches_played > 0 else 0, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating defensive metrics for team {team_id}: {e}")
            raise
    
    def calculate_player_form(self, player_id: int, last_n_matches: int = 5) -> Dict[str, Any]:
        """
        Calculate player form over last N matches.
        
        Args:
            player_id: Player ID
            last_n_matches: Number of recent matches to analyze
            
        Returns:
            Dictionary with form metrics
        """
        try:
            # Get recent player stats
            recent_stats = self.session.query(PlayerStats)\
                                     .join(Match, PlayerStats.match_id == Match.id)\
                                     .filter(PlayerStats.player_id == player_id)\
                                     .order_by(Match.utc_date.desc())\
                                     .limit(last_n_matches)\
                                     .all()
            
            if not recent_stats:
                return {"matches_analyzed": 0, "form_rating": 0.0}
            
            # Calculate form metrics
            total_goals = sum(stat.goals for stat in recent_stats)
            total_assists = sum(stat.assists for stat in recent_stats)
            total_minutes = sum(stat.minutes_played for stat in recent_stats)
            
            # Simple form rating based on goal contributions
            goal_contributions = total_goals + total_assists
            form_rating = goal_contributions / len(recent_stats) * 10  # Scale to 0-10
            
            return {
                "matches_analyzed": len(recent_stats),
                "goals": total_goals,
                "assists": total_assists,
                "goal_contributions": goal_contributions,
                "minutes_played": total_minutes,
                "form_rating": round(min(form_rating, 10.0), 2),  # Cap at 10
                "goals_per_game": round(total_goals / len(recent_stats), 2),
                "assists_per_game": round(total_assists / len(recent_stats), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating player form for player {player_id}: {e}")
            raise
    
    def calculate_team_momentum(self, team_id: int, last_n_matches: int = 10) -> Dict[str, Any]:
        """
        Calculate team momentum based on recent results.
        
        Args:
            team_id: Team ID
            last_n_matches: Number of recent matches to analyze
            
        Returns:
            Dictionary with momentum metrics
        """
        try:
            # Get recent matches
            recent_matches = self.session.query(Match)\
                                       .filter(
                                           or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                                           Match.status == "FINISHED"
                                       )\
                                       .order_by(Match.utc_date.desc())\
                                       .limit(last_n_matches)\
                                       .all()
            
            if not recent_matches:
                return {"matches_analyzed": 0, "momentum_score": 0.0}
            
            points = 0
            goals_for = 0
            goals_against = 0
            wins = draws = losses = 0
            
            # Weight recent matches more heavily
            for i, match in enumerate(recent_matches):
                weight = 1 + (i * 0.1)  # More recent matches get higher weight
                
                if match.home_team_id == team_id:
                    team_goals = match.score_full_time_home or 0
                    opponent_goals = match.score_full_time_away or 0
                else:
                    team_goals = match.score_full_time_away or 0
                    opponent_goals = match.score_full_time_home or 0
                
                goals_for += team_goals
                goals_against += opponent_goals
                
                # Calculate points with weighting
                if team_goals > opponent_goals:
                    points += 3 * weight
                    wins += 1
                elif team_goals == opponent_goals:
                    points += 1 * weight
                    draws += 1
                else:
                    losses += 1
            
            # Calculate momentum score (0-100)
            max_possible_points = sum(3 * (1 + (i * 0.1)) for i in range(len(recent_matches)))
            momentum_score = (points / max_possible_points) * 100 if max_possible_points > 0 else 0
            
            return {
                "matches_analyzed": len(recent_matches),
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_difference": goals_for - goals_against,
                "points": round(points, 2),
                "momentum_score": round(momentum_score, 2),
                "points_per_game": round(points / len(recent_matches) if recent_matches else 0, 2),
                "goals_per_game": round(goals_for / len(recent_matches) if recent_matches else 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating team momentum for team {team_id}: {e}")
            raise
    
    def calculate_head_to_head(self, team1_id: int, team2_id: int, last_n_matches: int = 10) -> Dict[str, Any]:
        """
        Calculate head-to-head statistics between two teams.
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            last_n_matches: Number of recent H2H matches to analyze
            
        Returns:
            Dictionary with head-to-head statistics
        """
        try:
            # Get head-to-head matches
            h2h_matches = self.session.query(Match)\
                                    .filter(
                                        or_(
                                            and_(Match.home_team_id == team1_id, Match.away_team_id == team2_id),
                                            and_(Match.home_team_id == team2_id, Match.away_team_id == team1_id)
                                        ),
                                        Match.status == "FINISHED"
                                    )\
                                    .order_by(Match.utc_date.desc())\
                                    .limit(last_n_matches)\
                                    .all()
            
            if not h2h_matches:
                return {"total_matches": 0}
            
            team1_wins = team1_draws = team1_losses = 0
            team1_goals_for = team1_goals_against = 0
            
            for match in h2h_matches:
                if match.home_team_id == team1_id:
                    # Team1 playing at home
                    team1_goals = match.score_full_time_home or 0
                    team2_goals = match.score_full_time_away or 0
                else:
                    # Team1 playing away
                    team1_goals = match.score_full_time_away or 0
                    team2_goals = match.score_full_time_home or 0
                
                team1_goals_for += team1_goals
                team1_goals_against += team2_goals
                
                if team1_goals > team2_goals:
                    team1_wins += 1
                elif team1_goals == team2_goals:
                    team1_draws += 1
                else:
                    team1_losses += 1
            
            return {
                "total_matches": len(h2h_matches),
                "team1_wins": team1_wins,
                "team1_draws": team1_draws,
                "team1_losses": team1_losses,
                "team2_wins": team1_losses,  # Team1's losses are Team2's wins
                "team1_goals_for": team1_goals_for,
                "team1_goals_against": team1_goals_against,
                "team2_goals_for": team1_goals_against,  # Team1's goals against are Team2's goals for
                "team2_goals_against": team1_goals_for,
                "team1_win_percentage": round(team1_wins / len(h2h_matches) * 100, 1),
                "team2_win_percentage": round(team1_losses / len(h2h_matches) * 100, 1),
                "draw_percentage": round(team1_draws / len(h2h_matches) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating head-to-head for teams {team1_id} vs {team2_id}: {e}")
            raise
    
    def calculate_league_power_rankings(self, league_id: int, season_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calculate power rankings for teams in a league based on multiple factors.
        
        Args:
            league_id: League ID
            season_year: Season year filter
            
        Returns:
            List of teams with power ranking scores
        """
        try:
            # Get all teams in the league
            teams = self.session.query(Team).filter(Team.league_id == league_id).all()
            
            if not teams:
                return []
            
            power_rankings = []
            
            for team in teams:
                try:
                    # Get basic metrics
                    from soccer_analytics.analytics.metrics import AnalyticsEngine
                    analytics = AnalyticsEngine(self.session)
                    team_metrics = analytics.calculate_team_metrics(team.id, season_year)
                    
                    if team_metrics.get("matches_played", 0) == 0:
                        continue
                    
                    # Get advanced metrics
                    momentum = self.calculate_team_momentum(team.id, 5)
                    possession = self.calculate_possession_metrics(team.id, season_year)
                    defensive = self.calculate_defensive_metrics(team.id, season_year)
                    
                    # Calculate power score (0-100)
                    # Weight different factors
                    points_factor = team_metrics.get("points_per_game", 0) * 15  # Max 45 points
                    goal_diff_factor = max(min(team_metrics.get("goal_difference", 0) / 2, 15), -15)  # ±15 points
                    momentum_factor = momentum.get("momentum_score", 0) * 0.3  # Max 30 points
                    form_factor = min(team_metrics.get("win_rate", 0) * 25, 25)  # Max 25 points
                    
                    power_score = points_factor + goal_diff_factor + momentum_factor + form_factor
                    power_score = max(0, min(100, power_score))  # Clamp to 0-100
                    
                    power_rankings.append({
                        "team_id": team.id,
                        "team_name": team.name,
                        "power_score": round(power_score, 2),
                        "points_per_game": team_metrics.get("points_per_game", 0),
                        "goal_difference": team_metrics.get("goal_difference", 0),
                        "momentum_score": momentum.get("momentum_score", 0),
                        "win_rate": team_metrics.get("win_rate", 0),
                        "matches_played": team_metrics.get("matches_played", 0)
                    })
                    
                except Exception as e:
                    logger.warning(f"Error calculating power ranking for team {team.name}: {e}")
                    continue
            
            # Sort by power score
            power_rankings.sort(key=lambda x: x["power_score"], reverse=True)
            
            # Add ranking position
            for i, ranking in enumerate(power_rankings, 1):
                ranking["power_ranking"] = i
            
            return power_rankings
            
        except Exception as e:
            logger.error(f"Error calculating league power rankings for league {league_id}: {e}")
            raise
    
    def calculate_player_efficiency(self, player_id: int, season_year: Optional[int] = None) -> Dict[str, float]:
        """
        Calculate player efficiency metrics.
        
        Args:
            player_id: Player ID
            season_year: Season year filter
            
        Returns:
            Dictionary with efficiency metrics
        """
        try:
            # Get player stats
            query = self.session.query(PlayerStats).filter(PlayerStats.player_id == player_id)
            
            if season_year:
                query = query.join(Match, PlayerStats.match_id == Match.id)\
                             .filter(func.extract('year', Match.season_start_date) == season_year)
            
            player_stats = query.all()
            
            if not player_stats:
                return {}
            
            # Calculate efficiency metrics
            total_minutes = sum(stat.minutes_played for stat in player_stats)
            total_goals = sum(stat.goals for stat in player_stats)
            total_assists = sum(stat.assists for stat in player_stats)
            total_shots = sum(stat.shots_total for stat in player_stats)
            total_shots_on_target = sum(stat.shots_on_target for stat in player_stats)
            total_passes = sum(stat.passes_total for stat in player_stats)
            total_passes_completed = sum(stat.passes_completed for stat in player_stats)
            
            if total_minutes == 0:
                return {}
            
            # Calculate per 90 minutes metrics
            minutes_per_90 = total_minutes / 90
            
            return {
                "goals_per_90": round(total_goals / minutes_per_90, 2) if minutes_per_90 > 0 else 0,
                "assists_per_90": round(total_assists / minutes_per_90, 2) if minutes_per_90 > 0 else 0,
                "goal_contributions_per_90": round((total_goals + total_assists) / minutes_per_90, 2) if minutes_per_90 > 0 else 0,
                "shots_per_90": round(total_shots / minutes_per_90, 2) if minutes_per_90 > 0 else 0,
                "shot_conversion_rate": round(total_goals / total_shots * 100, 1) if total_shots > 0 else 0,
                "shot_accuracy": round(total_shots_on_target / total_shots * 100, 1) if total_shots > 0 else 0,
                "pass_accuracy": round(total_passes_completed / total_passes * 100, 1) if total_passes > 0 else 0,
                "passes_per_90": round(total_passes / minutes_per_90, 1) if minutes_per_90 > 0 else 0,
                "total_minutes": total_minutes,
                "matches_played": len(player_stats)
            }
            
        except Exception as e:
            logger.error(f"Error calculating player efficiency for player {player_id}: {e}")
            raise