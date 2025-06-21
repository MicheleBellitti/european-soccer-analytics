#!/usr/bin/env python3
"""Test script to verify Football Data API connectivity and functionality."""

import logging
import sys
from soccer_analytics.etl.fetch import FootballDataFetcher, FootballDataAPIError
from soccer_analytics.config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_connection():
    """Test basic API connection and fetch competitions."""
    
    logger.info("Testing Football Data API connection...")
    logger.info(f"API Key (first 10 chars): {settings.football_data_api_key[:10]}...")
    logger.info(f"Base URL: {settings.football_data_base_url}")
    
    try:
        # Initialize fetcher
        fetcher = FootballDataFetcher()
        
        # Test fetching competitions
        logger.info("Fetching competitions...")
        competitions = fetcher.fetch_competitions()
        
        if competitions:
            logger.info(f"✅ Successfully fetched {len(competitions)} competitions")
            
            # Display first few competitions
            for i, comp in enumerate(competitions[:3]):
                logger.info(f"  {i+1}. {comp.get('name', 'Unknown')} ({comp.get('area', {}).get('name', 'Unknown')})")
            
            # Test fetching teams for Premier League (if available)
            premier_league_id = 2021
            try:
                logger.info(f"Testing team fetch for Premier League (ID: {premier_league_id})...")
                teams = fetcher.fetch_competition_teams(premier_league_id)
                logger.info(f"✅ Successfully fetched {len(teams)} teams for Premier League")
                
                if teams:
                    for i, team in enumerate(teams[:3]):
                        logger.info(f"  {i+1}. {team.get('name', 'Unknown')}")
                        
            except FootballDataAPIError as e:
                logger.warning(f"⚠️  Could not fetch Premier League teams: {e}")
                
        else:
            logger.error("❌ No competitions fetched")
            return False
            
        return True
        
    except FootballDataAPIError as e:
        logger.error(f"❌ API Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_api_limits():
    """Test API rate limits and provide guidance."""
    
    logger.info("\n📋 API Usage Information:")
    logger.info("- Free tier: 10 requests per minute")
    logger.info("- Free tier: Access to competitions, teams, matches")
    logger.info("- For production use, consider upgrading to paid tier")
    logger.info("- Rate limiting is handled automatically in the fetcher")

if __name__ == "__main__":
    print("🏈 European Soccer Analytics - API Test")
    print("=" * 50)
    
    # Check if API key is set
    if not settings.football_data_api_key or settings.football_data_api_key == "demo_key":
        print("⚠️  WARNING: Using demo API key!")
        print("Please set FOOTBALL_DATA_API_KEY environment variable")
        print("Get your free API key from: https://www.football-data.org/client/register")
        print("")
    
    # Run tests
    success = test_api_connection()
    test_api_limits()
    
    if success:
        print("\n✅ API test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ API test failed!")
        sys.exit(1) 