#!/usr/bin/env python3
"""Health check script for European Soccer Analytics platform."""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from soccer_analytics.config.database import check_db_connection
from soccer_analytics.etl.fetch import FootballDataFetcher, FootballDataAPIError
from soccer_analytics.config.settings import settings


def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic functionality."""
    result = {
        "status": "unknown",
        "connection": False,
        "tables_exist": False,
        "record_counts": {},
        "errors": []
    }
    
    try:
        # Test connection
        result["connection"] = check_db_connection()
        
        if result["connection"]:
            from soccer_analytics.config.database import get_db_session
            from soccer_analytics.data_models.models import League, Team, Player, Match, PlayerStats, TeamStats
            
            # Check table existence and record counts
            with get_db_session() as session:
                models = [
                    ("leagues", League),
                    ("teams", Team),
                    ("players", Player),
                    ("matches", Match),
                    ("player_stats", PlayerStats),
                    ("team_stats", TeamStats)
                ]
                
                all_tables_exist = True
                for table_name, model_class in models:
                    try:
                        count = session.query(model_class).count()
                        result["record_counts"][table_name] = count
                    except Exception as e:
                        all_tables_exist = False
                        result["errors"].append(f"Table {table_name} error: {str(e)}")
                
                result["tables_exist"] = all_tables_exist
            
            result["status"] = "healthy" if result["tables_exist"] else "degraded"
        else:
            result["status"] = "unhealthy"
            result["errors"].append("Database connection failed")
    
    except Exception as e:
        result["status"] = "unhealthy"
        result["errors"].append(f"Database check error: {str(e)}")
    
    return result


def check_api_health() -> Dict[str, Any]:
    """Check Football Data API connectivity and functionality."""
    result = {
        "status": "unknown",
        "connection": False,
        "rate_limit_ok": True,
        "competitions_count": 0,
        "response_time": None,
        "errors": []
    }
    
    try:
        fetcher = FootballDataFetcher()
        
        # Test basic API call and measure response time
        start_time = time.time()
        competitions = fetcher.fetch_competitions()
        end_time = time.time()
        
        result["response_time"] = round(end_time - start_time, 2)
        result["connection"] = True
        result["competitions_count"] = len(competitions)
        
        # Check response time (should be under 10 seconds)
        if result["response_time"] > 10:
            result["errors"].append(f"Slow API response: {result['response_time']}s")
            result["status"] = "degraded"
        else:
            result["status"] = "healthy"
    
    except FootballDataAPIError as e:
        result["status"] = "unhealthy"
        result["connection"] = False
        if "rate limit" in str(e).lower():
            result["rate_limit_ok"] = False
            result["errors"].append("API rate limit exceeded")
        elif "invalid" in str(e).lower():
            result["errors"].append("Invalid API key")
        else:
            result["errors"].append(f"API error: {str(e)}")
    
    except Exception as e:
        result["status"] = "unhealthy"
        result["connection"] = False
        result["errors"].append(f"API check error: {str(e)}")
    
    return result


def check_data_freshness() -> Dict[str, Any]:
    """Check if data is fresh and up-to-date."""
    result = {
        "status": "unknown",
        "last_match_update": None,
        "last_standings_update": None,
        "hours_since_match_update": None,
        "hours_since_standings_update": None,
        "is_fresh": False,
        "errors": []
    }
    
    try:
        from soccer_analytics.config.database import get_db_session
        from soccer_analytics.data_models.models import Match, TeamStats
        
        with get_db_session() as session:
            # Check latest match update
            latest_match = session.query(Match).order_by(Match.updated_at.desc()).first()
            if latest_match:
                result["last_match_update"] = latest_match.updated_at.isoformat()
                hours_diff = (datetime.now() - latest_match.updated_at).total_seconds() / 3600
                result["hours_since_match_update"] = round(hours_diff, 1)
            
            # Check latest standings update
            latest_standings = session.query(TeamStats).order_by(TeamStats.updated_at.desc()).first()
            if latest_standings:
                result["last_standings_update"] = latest_standings.updated_at.isoformat()
                hours_diff = (datetime.now() - latest_standings.updated_at).total_seconds() / 3600
                result["hours_since_standings_update"] = round(hours_diff, 1)
            
            # Data is considered fresh if updated within last 24 hours
            match_fresh = result["hours_since_match_update"] and result["hours_since_match_update"] < 24
            standings_fresh = result["hours_since_standings_update"] and result["hours_since_standings_update"] < 24
            
            result["is_fresh"] = match_fresh and standings_fresh
            
            if result["is_fresh"]:
                result["status"] = "healthy"
            elif match_fresh or standings_fresh:
                result["status"] = "degraded"
                result["errors"].append("Some data is stale")
            else:
                result["status"] = "unhealthy"
                result["errors"].append("All data is stale")
    
    except Exception as e:
        result["status"] = "unhealthy"
        result["errors"].append(f"Data freshness check error: {str(e)}")
    
    return result


def check_dashboard_health() -> Dict[str, Any]:
    """Check if dashboard components are working."""
    result = {
        "status": "unknown",
        "pages_exist": False,
        "imports_work": False,
        "errors": []
    }
    
    try:
        import os
        
        # Check if dashboard pages exist
        pages_dir = "src/soccer_analytics/dashboard/pages"
        required_pages = ["01_League_Overview.py", "02_Team_Analysis.py", "03_Player_Search.py"]
        
        missing_pages = []
        for page in required_pages:
            if not os.path.exists(os.path.join(pages_dir, page)):
                missing_pages.append(page)
        
        result["pages_exist"] = len(missing_pages) == 0
        
        if missing_pages:
            result["errors"].append(f"Missing dashboard pages: {missing_pages}")
        
        # Test imports
        try:
            from soccer_analytics.dashboard.utils import get_leagues
            from soccer_analytics.analytics.metrics import AnalyticsEngine
            result["imports_work"] = True
        except ImportError as e:
            result["imports_work"] = False
            result["errors"].append(f"Import error: {str(e)}")
        
        if result["pages_exist"] and result["imports_work"]:
            result["status"] = "healthy"
        elif result["pages_exist"] or result["imports_work"]:
            result["status"] = "degraded"
        else:
            result["status"] = "unhealthy"
    
    except Exception as e:
        result["status"] = "unhealthy"
        result["errors"].append(f"Dashboard check error: {str(e)}")
    
    return result


def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage."""
    result = {
        "status": "unknown",
        "disk_usage": None,
        "memory_info": None,
        "errors": []
    }
    
    try:
        import psutil
        
        # Check disk usage
        disk_usage = psutil.disk_usage('/')
        result["disk_usage"] = {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percent": round((disk_usage.used / disk_usage.total) * 100, 1)
        }
        
        # Check memory usage
        memory = psutil.virtual_memory()
        result["memory_info"] = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # Determine status based on resource usage
        disk_critical = result["disk_usage"]["percent"] > 90
        memory_critical = result["memory_info"]["percent"] > 90
        
        if disk_critical or memory_critical:
            result["status"] = "unhealthy"
            if disk_critical:
                result["errors"].append(f"Disk usage critical: {result['disk_usage']['percent']}%")
            if memory_critical:
                result["errors"].append(f"Memory usage critical: {result['memory_info']['percent']}%")
        elif result["disk_usage"]["percent"] > 80 or result["memory_info"]["percent"] > 80:
            result["status"] = "degraded"
            result["errors"].append("High resource usage")
        else:
            result["status"] = "healthy"
    
    except ImportError:
        result["status"] = "unknown"
        result["errors"].append("psutil not installed - cannot check system resources")
    except Exception as e:
        result["status"] = "unknown"
        result["errors"].append(f"System resource check error: {str(e)}")
    
    return result


def generate_health_report() -> Dict[str, Any]:
    """Generate comprehensive health report."""
    print("🏥 Running European Soccer Analytics Health Check...")
    
    health_checks = {
        "timestamp": datetime.now().isoformat(),
        "database": check_database_health(),
        "api": check_api_health(),
        "data_freshness": check_data_freshness(),
        "dashboard": check_dashboard_health(),
        "system_resources": check_system_resources()
    }
    
    # Calculate overall health
    statuses = [check["status"] for check in health_checks.values() if isinstance(check, dict) and "status" in check]
    
    if all(status == "healthy" for status in statuses):
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    health_checks["overall_status"] = overall_status
    
    return health_checks


def print_health_summary(health_report: Dict[str, Any]):
    """Print a human-readable health summary."""
    print(f"\n📊 Health Check Report - {health_report['timestamp']}")
    print("=" * 60)
    
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌",
        "unknown": "❓"
    }
    
    overall_emoji = status_emoji.get(health_report["overall_status"], "❓")
    print(f"\n{overall_emoji} Overall Status: {health_report['overall_status'].upper()}")
    
    print("\nComponent Status:")
    for component, details in health_report.items():
        if isinstance(details, dict) and "status" in details:
            emoji = status_emoji.get(details["status"], "❓")
            print(f"  {emoji} {component.replace('_', ' ').title()}: {details['status']}")
            
            if details.get("errors"):
                for error in details["errors"]:
                    print(f"     ⚠️  {error}")
    
    # Data summary
    db_data = health_report.get("database", {})
    if db_data.get("record_counts"):
        print("\n📈 Data Summary:")
        for table, count in db_data["record_counts"].items():
            print(f"  • {table}: {count:,} records")
    
    # API info
    api_data = health_report.get("api", {})
    if api_data.get("connection"):
        print(f"\n🌐 API Status:")
        print(f"  • Response time: {api_data.get('response_time', 'N/A')}s")
        print(f"  • Competitions: {api_data.get('competitions_count', 0)}")
    
    # Data freshness
    freshness_data = health_report.get("data_freshness", {})
    if freshness_data.get("hours_since_match_update") is not None:
        print(f"\n🕒 Data Freshness:")
        print(f"  • Last match update: {freshness_data['hours_since_match_update']} hours ago")
        if freshness_data.get("hours_since_standings_update") is not None:
            print(f"  • Last standings update: {freshness_data['hours_since_standings_update']} hours ago")


def main():
    """Main health check function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="European Soccer Analytics Health Check")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--exit-code", action="store_true", help="Exit with non-zero code if unhealthy")
    
    args = parser.parse_args()
    
    # Generate health report
    health_report = generate_health_report()
    
    if args.json:
        print(json.dumps(health_report, indent=2))
    else:
        print_health_summary(health_report)
    
    # Exit with appropriate code
    if args.exit_code:
        if health_report["overall_status"] == "unhealthy":
            sys.exit(1)
        elif health_report["overall_status"] == "degraded":
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main() 