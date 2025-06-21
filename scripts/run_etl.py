#!/usr/bin/env python3
"""ETL script for fetching and loading European Soccer data."""

import argparse
import logging
import sys
from typing import List

from soccer_analytics.config.database import init_db, check_db_connection
from soccer_analytics.etl import FootballDataFetcher, DataLoader, MAJOR_COMPETITIONS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_and_load_competitions(fetcher: FootballDataFetcher, loader: DataLoader) -> None:
    """Fetch and load competition data."""
    logger.info("Fetching and loading competitions...")
    
    try:
        competitions = fetcher.fetch_competitions()
        created, updated = loader.load_competitions(competitions)
        logger.info(f"Competitions loaded: {created} created, {updated} updated")
    except Exception as e:
        logger.error(f"Failed to fetch/load competitions: {e}")
        raise


def fetch_and_load_teams(fetcher: FootballDataFetcher, loader: DataLoader, competition_ids: List[int]) -> None:
    """Fetch and load team data for specified competitions."""
    logger.info(f"Fetching and loading teams for {len(competition_ids)} competitions...")
    
    total_created = 0
    total_updated = 0
    
    for comp_id in competition_ids:
        try:
            teams = fetcher.fetch_competition_teams(comp_id)
            
            # Get the league from database to get its internal ID
            from soccer_analytics.etl.load import get_league_by_external_id
            league = get_league_by_external_id(comp_id)
            
            if league:
                created, updated = loader.load_teams(teams, league.id)
                total_created += created
                total_updated += updated
                logger.info(f"Teams loaded for competition {comp_id}: {created} created, {updated} updated")
            else:
                logger.warning(f"League not found for competition ID {comp_id}")
                
        except Exception as e:
            logger.error(f"Failed to fetch/load teams for competition {comp_id}: {e}")
            continue
    
    logger.info(f"Total teams loaded: {total_created} created, {total_updated} updated")


def fetch_and_load_matches(fetcher: FootballDataFetcher, loader: DataLoader, competition_ids: List[int]) -> None:
    """Fetch and load match data for specified competitions."""
    logger.info(f"Fetching and loading matches for {len(competition_ids)} competitions...")
    
    total_created = 0
    total_updated = 0
    
    for comp_id in competition_ids:
        try:
            matches = fetcher.fetch_competition_matches(comp_id)
            created, updated = loader.load_matches(matches)
            total_created += created
            total_updated += updated
            logger.info(f"Matches loaded for competition {comp_id}: {created} created, {updated} updated")
            
        except Exception as e:
            logger.error(f"Failed to fetch/load matches for competition {comp_id}: {e}")
            continue
    
    logger.info(f"Total matches loaded: {total_created} created, {total_updated} updated")


def fetch_and_load_standings(fetcher: FootballDataFetcher, loader: DataLoader, competition_ids: List[int]) -> None:
    """Fetch and load standings data for specified competitions."""
    logger.info(f"Fetching and loading standings for {len(competition_ids)} competitions...")
    
    total_created = 0
    total_updated = 0
    
    for comp_id in competition_ids:
        try:
            standings = fetcher.fetch_competition_standings(comp_id)
            created, updated = loader.load_standings(standings)
            total_created += created
            total_updated += updated
            logger.info(f"Standings loaded for competition {comp_id}: {created} created, {updated} updated")
            
        except Exception as e:
            logger.error(f"Failed to fetch/load standings for competition {comp_id}: {e}")
            continue
    
    logger.info(f"Total standings loaded: {total_created} created, {total_updated} updated")


def main():
    """Main ETL function."""
    parser = argparse.ArgumentParser(description="European Soccer Analytics ETL")
    parser.add_argument(
        "--competitions", 
        nargs="+", 
        default=list(MAJOR_COMPETITIONS.keys()),
        help="Competition names to process (default: all major competitions)"
    )
    parser.add_argument(
        "--skip-competitions", 
        action="store_true",
        help="Skip fetching competition data"
    )
    parser.add_argument(
        "--skip-teams", 
        action="store_true",
        help="Skip fetching team data"
    )
    parser.add_argument(
        "--skip-matches", 
        action="store_true",
        help="Skip fetching match data"
    )
    parser.add_argument(
        "--skip-standings", 
        action="store_true",
        help="Skip fetching standings data"
    )
    parser.add_argument(
        "--init-db", 
        action="store_true",
        help="Initialize database tables before running ETL"
    )
    
    args = parser.parse_args()
    
    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed. Please check your database configuration.")
        sys.exit(1)
    
    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        init_db()
    
    # Get competition IDs
    competition_ids = []
    for comp_name in args.competitions:
        comp_id = MAJOR_COMPETITIONS.get(comp_name.upper())
        if comp_id:
            competition_ids.append(comp_id)
        else:
            logger.warning(f"Unknown competition: {comp_name}")
    
    if not competition_ids:
        logger.error("No valid competitions specified")
        sys.exit(1)
    
    logger.info(f"Processing competitions: {[name for name in args.competitions if MAJOR_COMPETITIONS.get(name.upper())]}")
    
    # Initialize fetcher and loader
    fetcher = FootballDataFetcher()
    loader = DataLoader()
    
    try:
        # Fetch and load data
        if not args.skip_competitions:
            fetch_and_load_competitions(fetcher, loader)
        
        if not args.skip_teams:
            fetch_and_load_teams(fetcher, loader, competition_ids)
        
        if not args.skip_matches:
            fetch_and_load_matches(fetcher, loader, competition_ids)
        
        if not args.skip_standings:
            fetch_and_load_standings(fetcher, loader, competition_ids)
        
        logger.info("ETL process completed successfully!")
        
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 