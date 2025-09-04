# Scrapy settings for domain_scraper project
# Optimized for Domain.com.au rental property scraping

BOT_NAME = "domain_scraper"

SPIDER_MODULES = ["domain_scraper.spiders"]
NEWSPIDER_MODULE = "domain_scraper.spiders"

# Override the default user-agent to match working scrape_test.py
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Obey robots.txt rules (set to False to avoid blocking)
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings - conservative to avoid being blocked
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Additional settings to help with anti-bot protection
DOWNLOAD_TIMEOUT = 15
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Enable cookies for session management
COOKIES_ENABLED = True

# Override the default request headers to match working scrape_test.py
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True

# Configure item pipelines for data processing
ITEM_PIPELINES = {
    "domain_scraper.pipelines.DomainScraperPipeline": 300,
}

# Enable HTTP caching to avoid re-downloading pages
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # Cache for 1 hour
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# Logging settings
LOG_LEVEL = "DEBUG"  # More verbose logging for debugging
LOG_FILE = "scrapy.log"

# Additional debugging settings
COOKIES_DEBUG = True
TELNETCONSOLE_ENABLED = True
