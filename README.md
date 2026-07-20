# NYC Sublet Listings Scraper & Map Visualizer

Two Python scripts to scrape NYC short-term sublet listings and visualize them on an interactive map.

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install ChromeDriver (macOS)
brew install chromedriver

# Or download manually from: https://chromedriver.chromium.org/
```

**Requirements:**
- Python 3.8+
- Chrome browser
- ChromeDriver

---

## Scripts

### 0. `run_listings_pipeline.py` - Orchestrator (⭐ Start Here!)
Runs the complete pipeline end-to-end with a single command.

**Usage:**
```bash
python3 run_listings_pipeline.py
```

**What it does:**
1. Runs the scraper to get fresh listings
2. Generates the interactive map
3. Opens the map in your browser automatically

**Time:** ~2-3 minutes total

---

### 1. `scrape_listings.py` - Web Scraper
Scrapes listingsproject.com for NYC sublets matching your criteria.

**Features:**
- Filters for specific date ranges (currently Oct 4-19, 2026)
- Only finds /day or /week pricing (excludes monthly)
- Automatically deduplicates results
- Scrapes up to 40 pages or until no more listings found
- Saves results to `matching_listings.txt`

**Usage:**
```bash
python3 scrape_listings.py
```

**Customize dates:**
Edit lines 150-151 in the script:
```python
target_start = datetime(2026, 10, 4)  # Your start date
target_end = datetime(2026, 10, 19)   # Your end date
```

---

### 2. `visualize_listings.py` - Map Generator  
Creates an interactive HTML map from scraper results.

**Features:**
- Reads `matching_listings.txt` automatically
- Geocodes all locations to map coordinates
- **Finds nearby subway stations with walking distances**
- Generates interactive map with Leaflet.js
- Click any marker to see full listing details + transit info
- Direct links to original listings
- Works with any future scraper output

**Usage:**
```bash
python3 visualize_listings.py
```

This will:
1. Read `matching_listings.txt`
2. Geocode all locations (takes ~1 minute)
3. Generate `listings_map.html`
4. Open it in your browser to view the interactive map

---

## Quick Start (One Command!)

```bash
python3 run_listings_pipeline.py
```

This single command will:
1. Scrape all listings (~2 minutes)
2. Generate the interactive map (~1 minute)
3. Automatically open the map in your browser

**That's it!** The `listings_map.html` file will be ready to view.

---

## Manual Workflow (Step by Step)

If you prefer to run each step manually:

```bash
# Step 1: Scrape listings
python3 scrape_listings.py

# Step 2: Visualize on map
python3 visualize_listings.py

# Step 3: View the map
open listings_map.html
```

---

## Output Files

- **`matching_listings.txt`** - Raw scraper results (text format)
- **`listings_map.html`** - Interactive map (open in any browser)

---

## Features

### Scraper
✅ Automatic duplicate removal  
✅ Date overlap detection  
✅ Price type filtering (/day, /week only)  
✅ **🆕 Tracks new vs existing listings** across runs  
✅ **Automatically removes stale listings** that disappeared  
✅ Scrapes transportation info from each listing  
✅ Respects rate limits (1-3 second delays)  
✅ Handles pagination gracefully  
✅ Progress indicators  

### Map Visualizer
✅ **🟢🔵 Color-coded markers** (green = new, blue = existing)  
✅ **Status badges** in popups (NEW/EXISTING)  
✅ Automatic geocoding via OpenStreetMap  
✅ **🚇 Transportation info** from listing pages  
✅ Popup cards with full listing details  
✅ Direct links to original listings  
✅ Mobile-responsive design  
✅ No external dependencies (pure HTML/JS)  

---

## Customization

### Change Search Parameters

Edit `scrape_listings.py`:

**Date range:**
```python
target_start = datetime(2026, 10, 4)
target_end = datetime(2026, 10, 19)
```

**Price types (add /month):**
```python
if price_type not in ['day', 'week', 'month']:  # Add 'month'
    continue
```

**Number of pages:**
```python
max_pages = 40  # Increase or decrease
```

### Customize Map Appearance

Edit `visualize_listings.py`:

**Map style:**
Change the tile layer URL (line ~160):
```python
# Dark mode example:
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', ...)
```

**Marker colors:**
Add custom marker icons using Leaflet marker options

---

## Notes

- **Geocoding rate limit:** The visualizer waits 1 second between geocoding requests to respect OpenStreetMap API limits
- **Failed geocoding:** If a location can't be geocoded, it defaults to NYC center (40.7128, -74.0060)
- **Browser compatibility:** Map works in all modern browsers (Chrome, Firefox, Safari, Edge)
- **No API keys needed:** Both scripts use free, public APIs

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'selenium'" or other import errors**
```bash
pip install -r requirements.txt
```

**"chromedriver: command not found"**
```bash
brew install chromedriver
```

**Map shows all markers in one location**
- This means geocoding failed. Check your internet connection.
- The free Nominatim API has rate limits. The script already includes 1-second delays.

**No listings found**
- Check your date range - listings may not overlap
- Try expanding the date range or price types
- Verify the website structure hasn't changed

---

## License

MIT - Feel free to modify and reuse!
