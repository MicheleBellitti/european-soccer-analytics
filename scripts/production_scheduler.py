#!/usr/bin/env python3
"""Production scheduler for automated data fetching and system monitoring."""

import schedule
import time
import logging
import sys
import signal
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from soccer_analytics.etl import FootballDataFetcher, DataLoader, MAJOR_COMPETITIONS
from soccer_analytics.config.database import check_db_connection, init_db
from soccer_analytics.config.settings import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """System health monitoring and alerting."""
    
    def __init__(self):
        self.last_successful_fetch = None
        self.consecutive_failures = 0
        self.max_failures = 3
        
    def check_system_health(self) -> dict:
        """Perform comprehensive system health check."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "database": False,
            "api": False,
            "data_freshness": False,
            "overall": False
        }
        
        try:
            # Check database connection
            health_status["database"] = check_db_connection()
            logger.info(f"Database health: {'✅ OK' if health_status['database'] else '❌ FAILED'}")
            
            # Check API connectivity
            try:
                fetcher = FootballDataFetcher()
                competitions = fetcher.fetch_competitions()
                health_status["api"] = len(competitions) > 0
                logger.info(f"API health: {'✅ OK' if health_status['api'] else '❌ FAILED'}")
            except Exception as e:
                logger.error(f"API health check failed: {e}")
                health_status["api"] = False
            
            # Check data freshness (data should be less than 24 hours old)
            try:
                from soccer_analytics.config.database import get_db_session
                from soccer_analytics.data_models.models import Match
                
                with get_db_session() as session:
                    latest_match = session.query(Match).order_by(Match.created_at.desc()).first()
                    if latest_match:
                        time_diff = datetime.now() - latest_match.created_at
                        health_status["data_freshness"] = time_diff < timedelta(hours=24)
                    else:
                        health_status["data_freshness"] = False
                        
                logger.info(f"Data freshness: {'✅ OK' if health_status['data_freshness'] else '❌ STALE'}")
            except Exception as e:
                logger.error(f"Data freshness check failed: {e}")
                health_status["data_freshness"] = False
            
            # Overall health
            health_status["overall"] = all([
                health_status["database"],
                health_status["api"],
                health_status["data_freshness"]
            ])
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return health_status
    
    def send_alert(self, subject: str, message: str):
        """Send alert notification (placeholder for email/Slack/etc.)."""
        logger.warning(f"ALERT: {subject} - {message}")
        # TODO: Implement actual alerting (email, Slack, etc.)


class DataFetcher:
    """Automated data fetching with error handling and retries."""
    
    def __init__(self):
        self.fetcher = FootballDataFetcher()
        self.loader = DataLoader()
        self.health_monitor = HealthMonitor()
        
    def fetch_daily_data(self):
        """Fetch daily data updates."""
        logger.info("🚀 Starting daily data fetch...")
        
        try:
            # Check system health first
            health = self.health_monitor.check_system_health()
            if not health["database"]:
                logger.error("Database health check failed - aborting data fetch")
                return False
                
            if not health["api"]:
                logger.error("API health check failed - aborting data fetch")
                return False
            
            # Fetch competitions (quick update)
            logger.info("Fetching competitions...")
            competitions = self.fetcher.fetch_competitions()
            created, updated = self.loader.load_competitions(competitions)
            logger.info(f"Competitions: {created} created, {updated} updated")
            
            # Fetch recent matches for major competitions
            total_matches_created = 0
            total_matches_updated = 0
            
            for comp_name, comp_id in MAJOR_COMPETITIONS.items():
                try:
                    logger.info(f"Fetching recent matches for {comp_name}...")
                    
                    # Fetch matches from last 7 days
                    from datetime import datetime, timedelta
                    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    date_to = datetime.now().strftime("%Y-%m-%d")
                    
                    matches = self.fetcher.fetch_competition_matches(
                        comp_id, 
                        date_from=date_from, 
                        date_to=date_to
                    )
                    
                    created, updated = self.loader.load_matches(matches)
                    total_matches_created += created
                    total_matches_updated += updated
                    
                    logger.info(f"{comp_name}: {created} new matches, {updated} updated")
                    
                    # Small delay to respect rate limits
                    time.sleep(6)  # 10 requests per minute limit
                    
                except Exception as e:
                    logger.error(f"Failed to fetch matches for {comp_name}: {e}")
                    continue
            
            # Fetch standings for major competitions
            total_standings_created = 0
            total_standings_updated = 0
            
            for comp_name, comp_id in MAJOR_COMPETITIONS.items():
                try:
                    logger.info(f"Fetching standings for {comp_name}...")
                    standings = self.fetcher.fetch_competition_standings(comp_id)
                    created, updated = self.loader.load_standings(standings)
                    total_standings_created += created
                    total_standings_updated += updated
                    
                    logger.info(f"{comp_name} standings: {created} created, {updated} updated")
                    
                    # Small delay to respect rate limits
                    time.sleep(6)
                    
                except Exception as e:
                    logger.error(f"Failed to fetch standings for {comp_name}: {e}")
                    continue
            
            # Log summary
            logger.info(f"✅ Daily data fetch completed!")
            logger.info(f"Summary: {total_matches_created} new matches, {total_matches_updated} updated matches")
            logger.info(f"Summary: {total_standings_created} new standings, {total_standings_updated} updated standings")
            
            # Reset failure counter on success
            self.health_monitor.consecutive_failures = 0
            self.health_monitor.last_successful_fetch = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Daily data fetch failed: {e}")
            self.health_monitor.consecutive_failures += 1
            
            if self.health_monitor.consecutive_failures >= self.health_monitor.max_failures:
                self.health_monitor.send_alert(
                    "Data Fetch Failure",
                    f"Data fetching has failed {self.health_monitor.consecutive_failures} consecutive times. Last error: {e}"
                )
            
            return False
    
    def fetch_weekly_full_data(self):
        """Fetch comprehensive weekly data update."""
        logger.info("🚀 Starting weekly full data fetch...")
        
        try:
            # Fetch teams for all competitions (weekly update)
            for comp_name, comp_id in MAJOR_COMPETITIONS.items():
                try:
                    logger.info(f"Fetching teams for {comp_name}...")
                    teams = self.fetcher.fetch_competition_teams(comp_id)
                    
                    from soccer_analytics.etl.load import get_league_by_external_id
                    league = get_league_by_external_id(comp_id)
                    
                    if league:
                        created, updated = self.loader.load_teams(teams, league.id)
                        logger.info(f"{comp_name} teams: {created} created, {updated} updated")
                    
                    time.sleep(6)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Failed to fetch teams for {comp_name}: {e}")
                    continue
            
            logger.info("✅ Weekly full data fetch completed!")
            return True
            
        except Exception as e:
            logger.error(f"Weekly data fetch failed: {e}")
            return False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down scheduler...")
    sys.exit(0)


def main():
    """Main scheduler function."""
    logger.info("🚀 Starting European Soccer Analytics Production Scheduler")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize components
    data_fetcher = DataFetcher()
    health_monitor = HealthMonitor()
    
    # Schedule daily data fetch (6 AM every day)
    schedule.every().day.at("06:00").do(data_fetcher.fetch_daily_data)
    
    # Schedule weekly full data fetch (Sunday at 2 AM)
    schedule.every().sunday.at("02:00").do(data_fetcher.fetch_weekly_full_data)
    
    # Schedule health checks (every 15 minutes)
    schedule.every(15).minutes.do(health_monitor.check_system_health)
    
    # Initial health check
    health = health_monitor.check_system_health()
    if health["overall"]:
        logger.info("✅ Initial health check passed - system is healthy")
    else:
        logger.warning("⚠️ Initial health check failed - system may have issues")
    
    logger.info("📅 Scheduler started with the following schedule:")
    logger.info("  • Daily data fetch: 06:00 UTC")
    logger.info("  • Weekly full data fetch: Sunday 02:00 UTC")
    logger.info("  • Health checks: Every 15 minutes")
    
    # Main scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        health_monitor.send_alert("Scheduler Error", f"Production scheduler encountered an error: {e}")
    finally:
        logger.info("🛑 Scheduler shutdown complete")


if __name__ == "__main__":
    main() 