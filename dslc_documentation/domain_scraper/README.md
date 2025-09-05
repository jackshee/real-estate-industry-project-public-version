# Domain.com.au Rental Property Scraper (Scrapy)

A Scrapy-based web scraper for extracting detailed rental property listings from Domain.com.au. This scraper extracts **50+ attributes** per property including basic property information, detailed features, location data, market insights, demographics, and school information.

## Installation

Highly recommended to make a new virtual environment `venv`

1. Install required packages:
```bash
pip install -r requirements.txt 
```

2. Navigate to the project directory:
```bash
cd dslc_documentation/domain_scraper
```

3. Ensure you have the Victorian suburbs CSV file:
```bash
# The scraper expects this file to exist:
data/geo/vic_suburbs_postcodes.csv
```

## Usage

### Basic Usage

Run the spider to scrape all Victorian suburbs and save to JSON:
```bash
scrapy crawl domain_rental -o domain_rental_listings.json
```

Save to CSV format:
```bash
scrapy crawl domain_rental -o domain_rental_listings.csv
```

### Test with Limited Suburbs

To test with just a few suburbs, modify the spider in `domain_scraper/spiders/domain_spider.py`:
```python
# Change this line in start_requests method:
unique_suburbs = unique_suburbs.head(2)  # Limit to first 2 suburbs
```

### Advanced Usage

Run with custom settings:
```bash
scrapy crawl domain_rental -s DOWNLOAD_DELAY=2 -o output.json
```

Run with verbose logging:
```bash
scrapy crawl domain_rental -L INFO -o output.json
```

Run with item count limit:
```bash
scrapy crawl domain_rental -s CLOSESPIDER_ITEMCOUNT=100 -o output.json
```

## How the Scraper Works

### Data Extraction Process

1. **Suburb-Based Scraping**: Reads Victorian suburbs from `vic_suburbs_postcodes.csv`
2. **Dynamic Page Limits**: Automatically detects when no more listings are available (up to 50 pages per suburb)
3. **Dual Data Sources**: 
   - **Search Results Pages**: Basic property information from listing cards
   - **Individual Property Pages**: Detailed information from `__NEXT_DATA__` JSON
4. **School Information**: Extracts nearby schools with distance and type data
5. **Image Extraction**: Uses Selenium to access photo galleries

### HTML Structure Analysis

Domain.com.au uses **Next.js** with **Server-Side Rendering (SSR)**. Property data is embedded in the HTML as JSON within a `<script id="__NEXT_DATA__">` tag:

```html
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "componentProps": {
        "beds": 2,
        "baths": 1,
        "parking": 1,
        "schoolCatchment": {
          "schools": [...]
        },
        "suburbInsights": {...},
        "neighbourhoodInsights": {...}
      }
    }
  }
}
</script>
```

This approach provides:
- **Complete Data Access**: All property information in one structured JSON object
- **Rich Metadata**: Market insights, demographics, and school data not visible in rendered HTML
- **Consistent Schema**: Same structure across all property pages

## Data Attributes

The scraper extracts **50+ attributes** per property, organized into several categories:

### 1. **Core Property Features**
```json
{
  "property_features": "2,1,-", // Two bedroom, 1 bath, no parking 
  "property_type": "Apartment / Unit / Flat",
  "rental_price": "$650 per week"
}
```

### 2. **Address & Location**
```json
{
  "full_address": "201/394 Collins Street, Melbourne VIC 3000",
  "unit_number": "201",
  "street_number": "394",
  "street": "Collins Street",
  "suburb": "Melbourne",
  "postcode": "3000",
  "state_abbreviation": "vic",
  "latitude": -37.816819,
  "longitude": 144.9611835
}
```

### 3. **Property Details**
```json
{
  "description": "A prestigious Collins Street address...",
  "features_list": ["Built In Robes", "Ducted Cooling", "Gym"],
  "structured_features": [
    {"name": "Built in wardrobes", "category": "Indoor", "source": "advertiser"}
  ],
  "number_of_photos": 10,
  "image_urls": ["https://rimh2.domainstatic.com.au/..."]
}
```

### 4. **Market Insights**


These are based on the median for the dwelling type for the suburb. 

```json
{
  "median_rent_price": 550,
  "median_sold_price": 349000,
  "avg_days_on_market": 104,
  "renter_percentage": 0.697,
  "single_percentage": 0.763
}
```

### 5. **Neighbourhood Demographics**
```json
{
  "age_0_to_19": 0.068,
  "age_20_to_39": 0.588,
  "age_40_to_59": 0.281,
  "age_60_plus": 0.063,
  "family_percentage": 0.388,
  "owner_percentage": 0.283
}
```

### 6. **School Information** 🏫
```json
{
  "schools": [
    ["Yarra Primary School", "Government", "primary", 390.44],
    ["Trinity Catholic School", "Catholic", "primary", 526.29],
    ["Xavier College - Burke Hall", "Catholic", "combined", 805.81],
    ["Richmond High School", "Government", "secondary", 842.12]
  ]
}
```

### 7. **Agent & Agency Information**
```json
{
  "agent_name": "Sally Woodhouse",
  "agency_name": "Harcourts Melbourne City",
  "property_id": 17748643,
  "listing_url": "https://www.domain.com.au/201-394-collins-street-melbourne-vic-3000-17748643"
}
```

### 8. **Property History**
```json
{
  "first_listed_date": "2025-09-05T10:41:44.547",
  "last_sold_date": null,
  "updated_date": "2025-09-05T10:41:44.55",
  "number_sold": 620
}
```

- **Processing Speed**: Approximately 1 property per 2-3 seconds (including individual page scraping)
- **Rate Limiting**: Built-in throttling to avoid being blocked
- **Error Handling**: Robust retry logic for failed requests
- **Memory Efficient**: Processes data incrementally
- **Scalable**: Can handle thousands of properties across all Victorian suburbs

## Configuration

### Settings
The scraper is configured in `domain_scraper/settings.py` with:
- Conservative rate limiting (1 request per second)
- Anti-bot protection headers
- Automatic retry on failures
- HTTP caching enabled
- Data validation pipelines

### Customization
You can customize the scraper by:
1. Modifying suburb limits in `domain_spider.py`
2. Adjusting rate limiting in `settings.py`
3. Adding new data fields in `items.py`
4. Customizing data processing in `pipelines.py`

### Logs
Check the `scrapy.log` file for detailed information about the scraping process.

## Files

- `domain_scraper/spiders/domain_spider.py` - Main spider logic
- `domain_scraper/items.py` - Data structure definition (50+ fields)
- `domain_scraper/pipelines.py` - Data processing and validation
- `domain_scraper/settings.py` - Scrapy configuration
- `school_scraping_analysis.md` - Detailed school data documentation
- `domain_rental_attributes_documentation.md` - Complete attribute reference
- `listing_analysis_report.md` - HTML structure analysis
