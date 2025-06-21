"""ETL (Extract, Transform, Load) module for European Soccer Analytics."""

from .fetch import FootballDataFetcher, FootballDataAPIError, MAJOR_COMPETITIONS
from .load import DataLoader

__all__ = [
    "FootballDataFetcher",
    "FootballDataAPIError", 
    "DataLoader",
    "MAJOR_COMPETITIONS"
]