#!/usr/bin/env python3
"""
End-to-end orchestrator for NYC listings scraper and map visualizer.
Runs both scripts in sequence and opens the resulting map.
"""

import subprocess
import sys
import os


def run_command(description, command):
    """Run a shell command and handle errors."""
    print(f"\n{'=' * 80}")
    print(f"🔄 {description}")
    print(f"{'=' * 80}\n")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=False
        )
        print(f"\n✓ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error in {description}")
        print(f"Exit code: {e.returncode}")
        return False


def main():
    """Run the complete pipeline."""
    print("\n" + "=" * 80)
    print("🗽 NYC SUBLET LISTINGS - COMPLETE PIPELINE")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Scrape listings from listingsproject.com")
    print("  2. Generate an interactive map")
    print("  3. Open the map in your browser")
    print()
    print("⏱️  Estimated time: 2-3 minutes")
    print("=" * 80)

    # Step 1: Run the scraper
    if not run_command(
        "Step 1: Scraping listings",
        "python3 scrape_listings.py"
    ):
        print("\n❌ Pipeline failed at scraping step")
        sys.exit(1)

    # Check if scraper produced output
    if not os.path.exists("matching_listings.txt"):
        print("\n❌ Error: matching_listings.txt not found")
        sys.exit(1)

    # Step 2: Generate the map
    if not run_command(
        "Step 2: Generating interactive map",
        "python3 visualize_listings.py"
    ):
        print("\n❌ Pipeline failed at visualization step")
        sys.exit(1)

    # Check if map was created
    if not os.path.exists("listings_map.html"):
        print("\n❌ Error: listings_map.html not found")
        sys.exit(1)

    # Step 3: Open the map
    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 80)
    print()
    print(f"✓ Scraped listings saved to: matching_listings.txt")
    print(f"✓ Interactive map saved to: listings_map.html")
    print()
    print("🌐 Opening map in your browser...")
    print("=" * 80)

    # Open the map in the default browser
    subprocess.run("open listings_map.html", shell=True)

    print("\n✨ Done! The map should now be open in your browser.\n")


if __name__ == "__main__":
    main()
