"""
Configuration file for NYC sublet scraper.
Edit these values to customize your search parameters.
"""
from datetime import datetime

# ============================================================================
# DATE RANGE - Change these to match your desired dates
# ============================================================================
TARGET_START_DATE = datetime(2026, 10, 4)   # Format: (year, month, day)
TARGET_END_DATE = datetime(2026, 10, 19)    # Format: (year, month, day)

# ============================================================================
# SCRAPING PARAMETERS
# ============================================================================
MAX_PAGES = 40  # Maximum number of pages to scrape
DELAY_BETWEEN_PAGES = 2  # Seconds to wait between page loads (respect rate limits)

# ============================================================================
# PRICE FILTERS
# ============================================================================
ALLOWED_PRICE_TYPES = ['day', 'week']  # Options: 'day', 'week', 'month'
