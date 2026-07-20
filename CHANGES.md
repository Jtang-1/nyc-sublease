# Recent Updates - New vs Existing Listings Tracking

## Overview
The scraper now tracks which listings are new vs existing across runs, and the map color-codes them for easy identification.

## Changes Made

### 1. `scrape_listings.py` Updates

**New Features:**
- ✅ Loads existing listings from previous `matching_listings.txt` before scraping
- ✅ Compares new scrape results against previous listings
- ✅ Marks each listing as "new" or "existing"
- ✅ Groups listings in output file by status
- ✅ Removes stale listings (ones that disappeared from the site)
- ✅ Shows summary of new/existing/stale counts

**Output Format:**
```
NYC Short-Term Sublets (Oct 4-19, 2026)
================================================================================
Total: 13 listings (5 new, 8 existing)
================================================================================

================================================================================
NEW LISTINGS
================================================================================

--- Listing 1 ---
Status: new
Title: Beautiful Park Slope Apartment
Price: $325/day
...

================================================================================
EXISTING LISTINGS
================================================================================

--- Listing 1 ---
Status: existing
Title: Modern, Spacious Apt in Clinton Hill
Price: $950/week
...
```

### 2. `visualize_listings.py` Updates

**New Features:**
- ✅ Reads the `Status:` field from listings
- ✅ Color-codes markers: 🟢 Green for new, 🔵 Blue for existing
- ✅ Shows status badge in popups ("🆕 NEW" or "♻️ EXISTING")
- ✅ Displays counts in header (e.g., "🟢 5 New  🔵 8 Existing")
- ✅ Backward compatible - defaults to "existing" for old files without status field

**Marker Colors:**
- 🟢 **Green markers** = New listings (not seen in previous scrape)
- 🔵 **Blue markers** = Existing listings (seen before)

### 3. Stale Listing Removal

**How it works:**
1. First scrape: All 13 listings marked as "new"
2. Second scrape: 
   - 8 listings still available → marked as "existing"
   - 5 new listings found → marked as "new"
   - 0 disappeared → removed from output
3. Summary shows: "5 new, 8 existing, 0 stale removed"

## Usage

### First Run
```bash
cd nyc_sublease
python3 run_listings_pipeline.py
```
- All listings will be marked as "new" (green markers)
- Creates `matching_listings.txt` with status fields

### Subsequent Runs
```bash
python3 run_listings_pipeline.py
```
- Compares against previous `matching_listings.txt`
- New listings → green markers
- Existing listings → blue markers  
- Stale listings → automatically removed

## Terminal Output Example

```
📊 Summary: 5 new listings, 8 existing listings

🆕 NEW LISTINGS:
--- New Listing 1 ---
Title: Beautiful Park Slope Apartment
Price: $325/day
URL: https://...

♻️  EXISTING LISTINGS:
--- Existing Listing 1 ---
Title: Clinton Hill 2BR
Price: $950/week
URL: https://...

✓ Results saved to: matching_listings.txt
  → 5 new listings
  → 8 existing listings
  → 0 stale listings removed
```

## Map Legend

The map header now shows:
```
🗽 NYC Short-Term Sublets Map
October 4-19, 2026 • 13 listings total
🟢 5 New    🔵 8 Existing
```

## Technical Details

### Tracking Method
- Uses listing URL as unique identifier
- Loads all URLs from previous `matching_listings.txt`
- Compares scraped URLs against loaded set
- Status determined by set membership test

### Backward Compatibility
- Old `matching_listings.txt` files without `Status:` field work fine
- Will treat all as "existing" on first run with new version
- Next run will properly detect new vs existing

### File Format
Each listing now includes:
```
Status: new          # or "existing"
Title: ...
Price: ...
...
```

This field is used by the visualizer to determine marker color.
