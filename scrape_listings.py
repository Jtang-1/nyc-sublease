#!/usr/bin/env python3
"""
Scrape Listings Project for short-term NYC sublets.
Filters for listings with /day or /week pricing that overlap with target dates.
Uses Selenium to handle JavaScript-rendered content.

Configuration: Edit config.py to change target dates and search parameters.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re
import time
import urllib.request

# Import configuration
from config import TARGET_START_DATE, TARGET_END_DATE, MAX_PAGES, ALLOWED_PRICE_TYPES


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string like 'July 17, 2026' to datetime object."""
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y")
    except ValueError:
        return None


def check_availability_overlap(start_str: str, end_str: str,
                               target_start: datetime, target_end: datetime) -> bool:
    """Check if listing availability fully covers the target date range.

    Returns True only if the listing is available for the ENTIRE target period.
    Listing must start on or before target_start AND end on or after target_end.
    """
    listing_start = parse_date(start_str)
    listing_end = parse_date(end_str)

    if not listing_start or not listing_end:
        return False

    # Listing must fully contain the target period
    # listing_start <= target_start: listing starts before or on target start
    # listing_end >= target_end: listing ends after or on target end
    return listing_start <= target_start and listing_end >= target_end


def fetch_transportation_info(listing_url: str) -> str:
    """Fetch transportation information from the listing detail page."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        req = urllib.request.Request(listing_url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # Look for "Transportation" heading
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'transport' in heading.get_text(strip=True).lower():
                    # Get the parent container's full text
                    parent = heading.parent
                    if parent:
                        full_text = parent.get_text(strip=True)
                        # Remove the "Transportation" heading text itself
                        transport_text = full_text.replace('Transportation', '').strip()
                        if transport_text:
                            return transport_text

                    # Fallback: try next sibling (could be a text node)
                    next_node = heading.next_sibling
                    if next_node and isinstance(next_node, str):
                        transport_text = next_node.strip()
                        if transport_text:
                            return transport_text

            return ""

    except Exception as e:
        print(f"    Warning: Could not fetch transportation info: {e}")
        return ""


# Removed old extract_listing_info function - now handled in scrape_page


def get_driver():
    """Initialize and return Chrome driver with headless options."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_page(driver, page_num: int, target_start: datetime, target_end: datetime) -> tuple[List[Dict], bool]:
    """Scrape a single page for matching listings using Selenium.

    Returns:
        tuple: (list of matching listings, has_more_pages boolean)
    """
    url = f"https://www.listingsproject.com/real-estate/new-york-city/sublets?subcategories[]=apt_sublet&subcategories[]=house_sublet&previous=&keyword=&sort=default-order&page={page_num}"

    print(f"Scraping page {page_num}...")

    try:
        driver.get(url)

        # Wait for listings to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            time.sleep(3)  # Additional wait for dynamic content
        except TimeoutException:
            print(f"Timeout waiting for page {page_num} to load")
            return [], False

        # Get page source after JavaScript rendering
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        matching_listings = []

        # Find all listing links (they go to /listings/...)
        listing_links = soup.find_all('a', href=re.compile(r'^/listings/'))

        # Check if we've gone past the last page (no listings found)
        if len(listing_links) == 0:
            print(f"  No listings found - reached end of pages")
            return [], False

        print(f"  Found {len(listing_links)} listing links on page {page_num}")

        for link in listing_links:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                if not title or not href:
                    continue

                # Skip "See more" and "Read the full listing" links
                if title in ['See more', 'Read the full listing and contact details']:
                    continue

                # Navigate up to find the listing card container
                # The container has all the listing info as siblings
                container = link.find_parent()
                while container and container.name != 'body':
                    # Get all text in this container
                    text_content = container.get_text(separator=' ', strip=True)

                    # Check if this container has both price and dates (indicates we found the listing card)
                    has_price = re.search(r'\$[\d,]+\s*/\s*(day|week|month)', text_content, re.IGNORECASE)
                    has_date = re.search(r'[A-Z][a-z]+\s+\d+,\s+\d{4}\s*[-–]\s*[A-Z][a-z]+\s+\d+,\s+\d{4}', text_content)

                    if has_price and has_date:
                        # Found the right container
                        break

                    container = container.find_parent()

                if not container:
                    continue

                text_content = container.get_text(separator=' ', strip=True)

                # Extract price
                price_match = re.search(r'\$[\d,]+\s*/\s*(day|week|month)', text_content, re.IGNORECASE)
                if not price_match:
                    continue

                price_type = price_match.group(1).lower()

                # Filter: only allowed price types (configured in config.py)
                if price_type not in ALLOWED_PRICE_TYPES:
                    continue

                # Extract dates
                date_pattern = r'([A-Z][a-z]+\s+\d+,\s+\d{4})\s*[-–]\s*([A-Z][a-z]+\s+\d+,\s+\d{4})'
                date_match = re.search(date_pattern, text_content)

                if not date_match:
                    continue

                start_date_str, end_date_str = date_match.groups()

                # Check date overlap with target dates
                if not check_availability_overlap(start_date_str, end_date_str, target_start, target_end):
                    continue

                # Extract location (pattern: "Location, BOROUGH | Type | Features")
                # Look for neighborhood/borough pattern after the dates
                location_pattern = r'(?:' + re.escape(end_date_str) + r')\s+([^|]+?)\s*\|'
                location_match = re.search(location_pattern, text_content)
                if location_match:
                    location = location_match.group(1).strip()
                else:
                    # Fallback: look for any text before first pipe
                    fallback_match = re.search(r'([A-Z][^|]+?)\s*\|', text_content)
                    location = fallback_match.group(1).strip() if fallback_match else "NYC"

                # Build full URL
                full_url = f"https://www.listingsproject.com{href}" if not href.startswith('http') else href

                # Fetch transportation info from the detail page
                print(f"  ✓ Found match: {title[:50]}... | {price_match.group(0)}")
                print(f"    Fetching transportation info...")
                transportation = fetch_transportation_info(full_url)

                listing_info = {
                    'title': title,
                    'url': full_url,
                    'price': price_match.group(0),
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'location': location,
                    'transportation': transportation,
                    'full_text': text_content[:300],
                    'status': 'new'  # Will be updated in main() based on existing_urls
                }

                matching_listings.append(listing_info)

                # Small delay to avoid overwhelming the server
                time.sleep(0.5)

            except Exception as e:
                # Silent fail on individual listings
                continue

        return matching_listings, True

    except Exception as e:
        print(f"Error scraping page {page_num}: {e}")
        return [], False


def load_existing_listings(filename: str = "matching_listings.txt") -> set:
    """Load existing listing URLs from previous scrape."""
    existing_urls = set()

    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Extract all URLs
            url_matches = re.findall(r'URL: (https://www\.listingsproject\.com/listings/.+)', content)
            existing_urls = set(url_matches)

        if existing_urls:
            print(f"✓ Loaded {len(existing_urls)} existing listings from previous scrape")
    except FileNotFoundError:
        print("→ No previous listings found - all listings will be marked as new")

    return existing_urls


def main():
    """Main scraping function."""
    # Use dates from config.py
    target_start = TARGET_START_DATE
    target_end = TARGET_END_DATE

    print("=" * 80)
    print("Scraping Listings Project for Short-Term NYC Sublets")
    print(f"Target dates: {target_start.strftime('%B %d, %Y')} - {target_end.strftime('%B %d, %Y')}")
    print(f"Looking for: {', '.join(['/' + pt for pt in ALLOWED_PRICE_TYPES])} pricing")
    print("=" * 80)
    print()

    # Load existing listings for comparison
    existing_urls = load_existing_listings()

    # Initialize Selenium driver
    driver = None
    all_matching = []

    try:
        print("Initializing browser...")
        driver = get_driver()

        # Scrape pages until we reach the end or max pages
        page_num = 1

        while page_num <= MAX_PAGES:
            matches, has_more = scrape_page(driver, page_num, target_start, target_end)
            all_matching.extend(matches)

            # Stop if we've reached the end of available pages
            if not has_more:
                print(f"\nReached last page at page {page_num}")
                break

            # Be polite to the server
            time.sleep(1)
            page_num += 1

    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed.")

    # Deduplicate by URL (each listing has multiple links)
    seen_urls = set()
    unique_listings = []
    for listing in all_matching:
        if listing['url'] not in seen_urls:
            seen_urls.add(listing['url'])
            unique_listings.append(listing)

    all_matching = unique_listings

    # Mark listings as new or existing based on previous scrape
    new_count = 0
    existing_count = 0
    for listing in all_matching:
        if listing['url'] in existing_urls:
            listing['status'] = 'existing'
            existing_count += 1
        else:
            listing['status'] = 'new'
            new_count += 1

    print()
    print(f"📊 Summary: {new_count} new listings, {existing_count} existing listings")

    # Display results
    print()
    print("=" * 80)
    print(f"FOUND {len(all_matching)} MATCHING LISTINGS")
    print("=" * 80)
    print()

    # Group by status for display
    new_listings = [l for l in all_matching if l['status'] == 'new']
    existing_listings = [l for l in all_matching if l['status'] == 'existing']

    if new_listings:
        print("\n🆕 NEW LISTINGS:")
        for i, listing in enumerate(new_listings, 1):
            print(f"\n--- New Listing {i} ---")
            print(f"Title: {listing['title']}")
            print(f"Price: {listing['price']}")
            print(f"Available: {listing['start_date']} - {listing['end_date']}")
            print(f"Location: {listing['location']}")
            if listing.get('transportation'):
                print(f"Transportation: {listing['transportation']}")
            print(f"URL: {listing['url']}")

    if existing_listings:
        print("\n♻️  EXISTING LISTINGS:")
        for i, listing in enumerate(existing_listings, 1):
            print(f"\n--- Existing Listing {i} ---")
            print(f"Title: {listing['title']}")
            print(f"Price: {listing['price']}")
            print(f"URL: {listing['url']}")

    # Save to file - group by status
    output_file = "matching_listings.txt"
    with open(output_file, 'w') as f:
        f.write("NYC Short-Term Sublets (Oct 4-19, 2026)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total: {len(all_matching)} listings ({new_count} new, {existing_count} existing)\n")
        f.write("=" * 80 + "\n\n")

        # Write new listings first
        if new_listings:
            f.write("=" * 80 + "\n")
            f.write("NEW LISTINGS\n")
            f.write("=" * 80 + "\n")

            for i, listing in enumerate(new_listings, 1):
                f.write(f"\n--- Listing {i} ---\n")
                f.write(f"Status: new\n")
                f.write(f"Title: {listing['title']}\n")
                f.write(f"Price: {listing['price']}\n")
                f.write(f"Available: {listing['start_date']} - {listing['end_date']}\n")
                f.write(f"Location: {listing['location']}\n")
                if listing.get('transportation'):
                    f.write(f"Transportation: {listing['transportation']}\n")
                f.write(f"URL: {listing['url']}\n")
                if 'full_text' in listing:
                    f.write(f"Details: {listing['full_text'][:300]}\n")

        # Write existing listings
        if existing_listings:
            f.write("\n\n")
            f.write("=" * 80 + "\n")
            f.write("EXISTING LISTINGS\n")
            f.write("=" * 80 + "\n")

            for i, listing in enumerate(existing_listings, 1):
                f.write(f"\n--- Listing {i} ---\n")
                f.write(f"Status: existing\n")
                f.write(f"Title: {listing['title']}\n")
                f.write(f"Price: {listing['price']}\n")
                f.write(f"Available: {listing['start_date']} - {listing['end_date']}\n")
                f.write(f"Location: {listing['location']}\n")
                if listing.get('transportation'):
                    f.write(f"Transportation: {listing['transportation']}\n")
                f.write(f"URL: {listing['url']}\n")
                if 'full_text' in listing:
                    f.write(f"Details: {listing['full_text'][:300]}\n")

    print(f"\n\n✓ Results saved to: {output_file}")
    print(f"  → {new_count} new listings")
    print(f"  → {existing_count} existing listings")
    if len(existing_urls) > len(all_matching):
        stale_count = len(existing_urls) - existing_count
        print(f"  → {stale_count} stale listings removed")


if __name__ == "__main__":
    main()
