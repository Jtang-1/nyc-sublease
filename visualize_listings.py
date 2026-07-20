#!/usr/bin/env python3
"""
Generate an interactive map from scraper results.
Reads matching_listings.txt and creates an HTML map with clickable markers.
"""

import re
import time
import json
from typing import List, Dict, Optional
from urllib.parse import quote
import urllib.request


def parse_listings_file(filename: str) -> List[Dict]:
    """Parse the matching_listings.txt file into structured data."""
    listings = []

    with open(filename, 'r') as f:
        content = f.read()

    # Split by listing separators
    listing_blocks = re.split(r'\n--- Listing \d+ ---\n', content)

    for block in listing_blocks[1:]:  # Skip the header
        listing = {}

        # Extract status
        status_match = re.search(r'Status: (.+)', block)
        if status_match:
            listing['status'] = status_match.group(1).strip()
        else:
            listing['status'] = 'existing'  # Default for old format

        # Extract title
        title_match = re.search(r'Title: (.+)', block)
        if title_match:
            listing['title'] = title_match.group(1).strip()

        # Extract price
        price_match = re.search(r'Price: (.+)', block)
        if price_match:
            listing['price'] = price_match.group(1).strip()

        # Extract dates
        date_match = re.search(r'Available: (.+)', block)
        if date_match:
            listing['dates'] = date_match.group(1).strip()

        # Extract location
        location_match = re.search(r'Location: (.+)', block)
        if location_match:
            location_raw = location_match.group(1).strip()
            # Clean up location - extract just the neighborhood/borough
            # Remove everything before the last occurrence of a year (4 digits)
            year_split = re.split(r'\b\d{4}\b', location_raw)
            if len(year_split) > 1:
                # Take everything after the last year
                after_year = year_split[-1].strip()
                # Extract text before first pipe
                before_pipe = re.split(r'\s*\|', after_year)[0].strip()
                listing['location'] = before_pipe if before_pipe else "NYC"
            else:
                listing['location'] = location_raw

        # Extract URL
        url_match = re.search(r'URL: (.+)', block)
        if url_match:
            listing['url'] = url_match.group(1).strip()

        # Extract transportation
        transport_match = re.search(r'Transportation: (.+)', block)
        if transport_match:
            listing['transportation'] = transport_match.group(1).strip()
        else:
            listing['transportation'] = ""

        if listing.get('title') and listing.get('url'):
            listings.append(listing)

    return listings


def geocode_location(location: str) -> Optional[tuple]:
    """
    Geocode a location string to lat/lng using Nominatim (OpenStreetMap).
    Returns (lat, lng) or None if not found.
    """
    # Add "New York City" to help with geocoding
    query = f"{location}, New York City, NY"

    url = f"https://nominatim.openstreetmap.org/search?q={quote(query)}&format=json&limit=1"

    headers = {
        'User-Agent': 'ListingsMapVisualization/1.0'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        if data:
            return (float(data[0]['lat']), float(data[0]['lon']))
        else:
            print(f"  Warning: Could not geocode '{location}'")
            return None

    except Exception as e:
        print(f"  Error geocoding '{location}': {e}")
        return None


def geocode_all_listings(listings: List[Dict]) -> List[Dict]:
    """Geocode all listings and add lat/lng to each."""
    print("Geocoding locations...")

    for i, listing in enumerate(listings, 1):
        location = listing.get('location', '')
        print(f"  [{i}/{len(listings)}] Geocoding: {location}")

        coords = geocode_location(location)

        if coords:
            listing['lat'], listing['lng'] = coords
        else:
            # Default to NYC center if geocoding fails
            listing['lat'], listing['lng'] = 40.7128, -74.0060

        # Be respectful to the API - rate limit
        time.sleep(1)

    return listings


def generate_html_map(listings: List[Dict], output_file: str = "listings_map.html"):
    """Generate an interactive HTML map with Leaflet.js"""

    # Calculate center of map (average of all coordinates)
    if listings:
        avg_lat = sum(l['lat'] for l in listings) / len(listings)
        avg_lng = sum(l['lng'] for l in listings) / len(listings)
    else:
        avg_lat, avg_lng = 40.7128, -74.0060  # NYC default

    # Count new vs existing
    new_count = sum(1 for l in listings if l.get('status') == 'new')
    existing_count = sum(1 for l in listings if l.get('status') == 'existing')

    # Build markers JavaScript
    markers_js = []
    for listing in listings:
        # Escape single quotes in strings
        title = listing['title'].replace("'", "\\'").replace('"', '\\"')
        price = listing['price'].replace("'", "\\'")
        dates = listing['dates'].replace("'", "\\'")
        location = listing['location'].replace("'", "\\'")
        url = listing['url']
        status = listing.get('status', 'existing')

        # Determine marker color based on status
        if status == 'new':
            marker_color = '#10b981'  # Green for new
            status_badge = '<span style="display: inline-block; background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 8px;">🆕 NEW</span>'
        else:
            marker_color = '#3b82f6'  # Blue for existing
            status_badge = '<span style="display: inline-block; background: #3b82f6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 8px;">♻️ EXISTING</span>'

        # Build transit info HTML from scraped transportation field
        transit_html = ""
        if listing.get('transportation'):
            transport_text = listing['transportation'].replace("'", "\\'")
            transit_html = f'<p style="margin: 10px 0 0 0; padding-top: 8px; border-top: 1px solid #e5e7eb;"><strong>🚇 Transportation:</strong></p><p style="margin: 5px 0; font-size: 13px; color: #374151;">{transport_text}</p>'

        popup_html = f"""
        <div style="min-width: 280px; max-width: 350px;">
            {status_badge}
            <h3 style="margin: 0 0 10px 0; font-size: 14px; line-height: 1.4;">{title}</h3>
            <p style="margin: 5px 0;"><strong>💰 Price:</strong> {price}</p>
            <p style="margin: 5px 0;"><strong>📅 Available:</strong> {dates}</p>
            <p style="margin: 5px 0;"><strong>📍 Location:</strong> {location}</p>
            {transit_html}
            <p style="margin: 12px 0 0 0;">
                <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline; font-weight: 500;">
                    View Full Listing →
                </a>
            </p>
        </div>
        """

        # Create custom colored marker icon (simple circle with dot)
        marker_js = f"""
        var icon{id(listing)} = L.divIcon({{
            className: 'custom-marker',
            html: '<div style="background-color: {marker_color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        }});
        L.marker([{listing['lat']}, {listing['lng']}], {{icon: icon{id(listing)}}})
            .addTo(map)
            .bindPopup(`{popup_html}`);
        """
        markers_js.append(marker_js)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NYC Sublet Listings Map</title>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossorigin=""/>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin=""></script>

    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        #header {{
            background: #1e293b;
            color: white;
            padding: 20px;
            text-align: center;
        }}

        #header h1 {{
            margin: 0;
            font-size: 24px;
        }}

        #header p {{
            margin: 5px 0 0 0;
            color: #94a3b8;
            font-size: 14px;
        }}

        #map {{
            width: 100%;
            height: calc(100vh - 100px);
        }}

        .leaflet-popup-content {{
            margin: 15px;
        }}

        .leaflet-popup-content h3 {{
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🗽 NYC Short-Term Sublets Map</h1>
        <p>October 4-19, 2026 • {len(listings)} listings total</p>
        <div style="margin-top: 10px; font-size: 13px;">
            <span style="margin-right: 20px;">🟢 <strong>{new_count}</strong> New</span>
            <span>🔵 <strong>{existing_count}</strong> Existing</span>
        </div>
    </div>

    <div id="map"></div>

    <script>
        // Initialize map centered on NYC
        const map = L.map('map').setView([{avg_lat}, {avg_lng}], 12);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        // Add markers
        {chr(10).join(markers_js)}
    </script>
</body>
</html>"""

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"\n✓ Map generated: {output_file}")
    print(f"  Open it in your browser to view the interactive map!")


def main():
    """Main function to generate map from scraper output."""
    input_file = "matching_listings.txt"
    output_file = "listings_map.html"

    print("=" * 80)
    print("NYC Listings Map Generator")
    print("=" * 80)
    print()

    # Parse listings
    print(f"Reading listings from {input_file}...")
    listings = parse_listings_file(input_file)
    print(f"✓ Found {len(listings)} listings")
    print()

    if not listings:
        print("Error: No listings found in file")
        return

    # Geocode locations
    listings = geocode_all_listings(listings)
    print()

    # Generate map
    generate_html_map(listings, output_file)


if __name__ == "__main__":
    main()
