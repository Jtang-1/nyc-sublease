#!/usr/bin/env python3
"""
Unit tests for scrape_listings.py
Focus on date overlap logic to ensure listings fully cover target periods.
"""

import unittest
from datetime import datetime
from scrape_listings import check_availability_overlap, parse_date


class TestDateParsing(unittest.TestCase):
    """Test date parsing functionality."""

    def test_parse_valid_date(self):
        """Test parsing a valid date string."""
        result = parse_date("July 24, 2026")
        expected = datetime(2026, 7, 24)
        self.assertEqual(result, expected)

    def test_parse_invalid_date(self):
        """Test parsing an invalid date string."""
        result = parse_date("Invalid Date")
        self.assertIsNone(result)


class TestAvailabilityOverlap(unittest.TestCase):
    """Test availability overlap logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Target period: October 4-19, 2026
        self.target_start = datetime(2026, 10, 4)
        self.target_end = datetime(2026, 10, 19)

    def test_listing_ends_before_target_period_ends(self):
        """
        BUG TEST: Listing ends on Oct 10, but target period goes to Oct 19.
        This should return False because the listing doesn't cover the entire target period.
        """
        # Listing: July 24 - October 10, 2026
        listing_start = "July 24, 2026"
        listing_end = "October 10, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Listing ending Oct 10 should NOT match target period ending Oct 19")

    def test_exact_match(self):
        """Listing dates exactly match target dates."""
        listing_start = "October 4, 2026"
        listing_end = "October 19, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertTrue(result,
            "Exact date match should return True")

    def test_listing_covers_entire_target_period(self):
        """Listing starts before and ends after target period."""
        listing_start = "September 1, 2026"
        listing_end = "November 1, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertTrue(result,
            "Listing covering entire target period should return True")

    def test_listing_starts_after_target_starts(self):
        """Listing starts after target start but ends after target end."""
        listing_start = "October 10, 2026"
        listing_end = "November 1, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Listing starting Oct 10 should NOT match target starting Oct 4")

    def test_listing_ends_before_target_starts(self):
        """Listing ends before target period begins (no overlap)."""
        listing_start = "August 1, 2026"
        listing_end = "September 30, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Listing ending before target starts should return False")

    def test_listing_starts_after_target_ends(self):
        """Listing starts after target period ends (no overlap)."""
        listing_start = "October 20, 2026"
        listing_end = "November 20, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Listing starting after target ends should return False")

    def test_listing_same_start_but_ends_early(self):
        """Listing starts on target start but ends before target end."""
        listing_start = "October 4, 2026"
        listing_end = "October 15, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Listing ending Oct 15 should NOT match target ending Oct 19")

    def test_listing_starts_early_ends_on_target_end(self):
        """Listing starts before target but ends exactly on target end."""
        listing_start = "September 1, 2026"
        listing_end = "October 19, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertTrue(result,
            "Listing starting early and ending on target end should return True")

    def test_invalid_listing_dates(self):
        """Test with invalid date strings."""
        listing_start = "Invalid"
        listing_end = "Also Invalid"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Invalid dates should return False")

    def test_one_day_listing_within_target(self):
        """Single day listing within target period."""
        listing_start = "October 10, 2026"
        listing_end = "October 10, 2026"

        result = check_availability_overlap(
            listing_start, listing_end,
            self.target_start, self.target_end
        )

        self.assertFalse(result,
            "Single day listing should NOT match multi-day target period")


if __name__ == '__main__':
    unittest.main(verbosity=2)
