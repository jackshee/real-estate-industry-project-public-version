# Domain.com.au Rental Property Scraper (Scrapy)

This is a Scrapy-based web scraper for extracting rental property listings from Domain.com.au. It's equivalent to the `scrape_test.py` script but uses the Scrapy framework for better performance and reliability.

## Features

- Extracts property listings from Domain.com.au rental search results
- Scrapes multiple pages (configurable, default: 50 pages)
- Extracts the same data fields as `scrape_test.py`:
  - Listing title (price)
  - Address components (line 1, suburb, state, postcode)
  - Property features
  - Property type
- Built-in rate limiting and anti-bot protection
- Automatic retry on failures
- Data validation and cleaning
- Multiple output formats (JSON, CSV)

## Installation

1. Make sure you have Scrapy installed:
```bash
pip install scrapy
```

2. Navigate to the project directory:
```bash
cd domain_scraper
```

## Usage

### Basic Usage

Run the spider to scrape all pages and save to JSON:
```bash
scrapy crawl domain_rental -o domain_rental_listings.json
```

Save to CSV format:
```bash
scrapy crawl domain_rental -o domain_rental_listings.csv
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

### Test with Limited Pages

To test with just a few pages, modify the `start_requests` method in `domain_scraper/spiders/domain_spider.py`:
```python
# Change this line:
for page in range(1, 51):  # 50 pages
# To this for testing:
for page in range(1, 6):   # 5 pages
```

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
1. Modifying the number of pages in `domain_spider.py`
2. Adjusting rate limiting in `settings.py`
3. Adding new data fields in `items.py`
4. Customizing data processing in `pipelines.py`

## Output

The scraper outputs data in the same format as `scrape_test.py`:

```json
{
  "listing_title": "$500 per week",
  "address_line_1": "123 Main Street",
  "suburb": "Melbourne",
  "state": "VIC",
  "postcode": "3000",
  "property_features": "2 bed, 1 bath, 1 parking",
  "property_type": "House",
  "page_number": 1,
  "url": "https://www.domain.com.au/rent/?sort=price-asc&page=1"
}
```

## Performance

- Processes approximately 1 page per second
- Includes automatic throttling to avoid being blocked
- Uses HTTP caching to avoid re-downloading pages
- Built-in retry mechanism for failed requests

## Troubleshooting

### Common Issues

1. **Connection errors**: The scraper includes retry logic and rate limiting
2. **Empty results**: Check if the website structure has changed
3. **Blocked requests**: Increase `DOWNLOAD_DELAY` in settings

### Logs

Check the `scrapy.log` file for detailed information about the scraping process.

## Comparison with scrape_test.py

| Feature | scrape_test.py | Scrapy Version |
|---------|----------------|----------------|
| Framework | requests + BeautifulSoup | Scrapy |
| Rate Limiting | Manual (time.sleep) | Built-in AutoThrottle |
| Error Handling | Basic try/catch | Advanced retry logic |
| Caching | None | HTTP caching |
| Data Validation | Manual | Pipeline-based |
| Output Formats | JSON only | JSON, CSV, XML |
| Performance | Single-threaded | Optimized async |

## Files

- `domain_scraper/spiders/domain_spider.py` - Main spider logic
- `domain_scraper/items.py` - Data structure definition
- `domain_scraper/pipelines.py` - Data processing and validation
- `domain_scraper/settings.py` - Scrapy configuration
- `scrapy.cfg` - Scrapy project configuration
