"""
Domain.com.au Rental Property Scraper using Scrapy
Equivalent to scrape_test.py but using Scrapy framework

To run this spider:
cd domain_scraper
scrapy crawl domain_rental -o domain_rental_listings.json

Or to save as CSV:
scrapy crawl domain_rental -o domain_rental_listings.csv
"""

import scrapy
import re
import pandas as pd
import os
from urllib.parse import urlparse, parse_qs
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from ..items import DomainScraperItem


class DomainRentalSpider(scrapy.Spider):
    name = "domain_rental"
    allowed_domains = ["domain.com.au"]

    # Initialize suburb data
    def __init__(self):
        super().__init__()
        self.suburb_data = self._load_suburb_data()
        self.suburb_stats = {}  # Track listings per suburb
        self.current_suburb = None
        self.current_postcode = None
        self.current_page = 0
        self.total_listings = 0
        self.driver = None  # Selenium driver for image extraction

    def _load_suburb_data(self):
        """Load suburb and postcode data from CSV file"""
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "data",
            "geo",
            "vic_suburbs_postcodes.csv",
        )

        try:
            df = pd.read_csv(csv_path)
            # sort by suburb alphabetically
            df = df.sort_values(by="suburb")
            self.logger.info(f"Loaded {len(df)} suburb-postcode pairs from CSV")
            return df
        except Exception as e:
            self.logger.error(f"Error loading suburb data: {e}")
            return pd.DataFrame()

    # No longer using start_urls - will generate URLs dynamically
    start_urls = []

    # Custom settings for this spider
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "DOWNLOAD_DELAY": 1,  # 1 second delay between requests
        "RANDOMIZE_DOWNLOAD_DELAY": 0.5,  # Randomize delay by 0.5 seconds
        "CONCURRENT_REQUESTS": 1,  # Process one request at a time
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "AUTOTHROTTLE_DEBUG": True,
    }

    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver for image extraction"""
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Run in background
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("Selenium WebDriver initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
                self.driver = None

    def _close_selenium_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium WebDriver: {e}")

    def closed(self, reason):
        """Called when spider is closed"""
        self._close_selenium_driver()
        super().closed(reason)

    def start_requests(self):
        """Generate requests for each suburb's first page"""

        if self.suburb_data.empty:
            return

        # Get unique suburb-postcode combinations
        unique_suburbs = self.suburb_data.drop_duplicates(["suburb", "postcode"])

        # For testing, limit to Abbotsford only
        # Remove this line to process all suburbs
        unique_suburbs = unique_suburbs[
            unique_suburbs["suburb"].str.lower() == "abbotsford"
        ]
        self.logger.info(
            f"Processing {len(unique_suburbs)} suburbs (limited for testing)"
        )

        for idx, row in unique_suburbs.iterrows():
            suburb = row["suburb"].lower().replace(" ", "-")
            postcode = str(row["postcode"])

            # Generate URL for suburb's first page with ssubs=0 to exclude nearby suburbs
            url = f"https://www.domain.com.au/rent/{suburb}-vic-{postcode}/?ssubs=0&page=1"

            self.logger.info(
                f"Generating request for {row['suburb']} ({postcode}): {url}"
            )

            request = scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "suburb": row["suburb"],
                    "postcode": postcode,
                    "page_number": 1,
                    "suburb_url_base": f"https://www.domain.com.au/rent/{suburb}-vic-{postcode}/?ssubs=0",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
            )

            yield request

        self.logger.info("=== FINISHED SUBURB-BASED REQUESTS GENERATION ===")

    def scrape_listing(self, response):
        """
        Scrape individual listing page and extract detailed information
        """
        try:
            suburb = response.meta.get("suburb", "Unknown")
            postcode = response.meta.get("postcode", "Unknown")
            page_number = response.meta.get("page_number", 1)
            listing_index = response.meta.get("listing_index", 1)

            self.logger.info(
                f"=== SCRAPING LISTING {listing_index} DETAILS for {suburb} ({postcode}) ==="
            )
            self.logger.info(f"Listing URL: {response.url}")
            self.logger.info(f"Status Code: {response.status}")
            self.logger.info(f"Response Length: {len(response.body)} bytes")

            # Create item and add suburb/postcode metadata
            item = DomainScraperItem()
            item["suburb"] = suburb
            item["postcode"] = postcode
            item["url"] = response.url

            # Add property features from listing card
            item["property_features"] = response.meta.get("property_features", "")

            # Extract detailed info from the listing page
            self._extract_listing_page_data(item, response, listing_index)

            yield item

        except Exception as e:
            pass  # Silent error handling for performance

    def _extract_listing_page_data(self, item, response, listing_index):
        """Extract detailed data from the individual listing page"""

        # Extract data from the JSON structure in the page
        try:
            # Find the __NEXT_DATA__ script tag
            next_data_script = response.css("script#__NEXT_DATA__::text").get()
            if next_data_script:
                import json

                data = json.loads(next_data_script)

                # Extract property details from the JSON structure
                props = data.get("props", {})
                page_props = props.get("pageProps", {})
                component_props = page_props.get("componentProps", {})

                # Property type from JSON
                item["property_type"] = component_props.get("propertyType", "")

                # Address details
                item["full_address"] = component_props.get("address", "")
                item["unit_number"] = component_props.get("unitNumber", "")
                item["street_number"] = component_props.get("streetNumber", "")
                item["street"] = component_props.get("street", "")
                # Note: suburb and postcode are already set as scraped_suburb and scraped_postcode
                # These are the detailed values from the individual listing page
                item["state_abbreviation"] = component_props.get(
                    "stateAbbreviation", ""
                )

                # Property ID and URLs
                item["property_id"] = component_props.get("id", "")
                item["listing_url"] = component_props.get("listingUrl", "")

                # Agent and agency information
                agents = component_props.get("agents", [])
                if agents:
                    agent = agents[0]
                    item["agent_name"] = agent.get("name", "")

                item["agency_name"] = component_props.get("agencyName", "")

                # Property description
                description_list = component_props.get("description", [])
                if description_list:
                    item["description"] = " ".join(description_list).strip()

                # Property features
                features = component_props.get("features", [])
                if features:
                    item["features_list"] = features

                structured_features = component_props.get("structuredFeatures", [])
                if structured_features:
                    item["structured_features"] = structured_features

                # Price information
                listing_summary = component_props.get("listingSummary", {})
                if listing_summary:
                    item["rental_price"] = listing_summary.get("title", "")
                    item["listing_status"] = listing_summary.get("status", "")
                    item["listing_tag"] = listing_summary.get("tag", "")

                # Location coordinates
                map_data = component_props.get("map", {})
                if map_data:
                    item["latitude"] = map_data.get("latitude", "")
                    item["longitude"] = map_data.get("longitude", "")

                # Suburb insights (market data)
                suburb_insights = component_props.get("suburbInsights", {})
                if suburb_insights:
                    item["median_rent_price"] = suburb_insights.get(
                        "medianRentPrice", ""
                    )
                    item["median_sold_price"] = suburb_insights.get("medianPrice", "")
                    item["avg_days_on_market"] = suburb_insights.get(
                        "avgDaysOnMarket", ""
                    )
                    item["renter_percentage"] = suburb_insights.get(
                        "renterPercentage", ""
                    )
                    item["single_percentage"] = suburb_insights.get(
                        "singlePercentage", ""
                    )

                # Neighbourhood insights
                neighbourhood_insights = component_props.get(
                    "neighbourhoodInsights", {}
                )
                if neighbourhood_insights:
                    item["age_0_to_19"] = neighbourhood_insights.get("age0To19", "")
                    item["age_20_to_39"] = neighbourhood_insights.get("age20To39", "")
                    item["age_40_to_59"] = neighbourhood_insights.get("age40To59", "")
                    item["age_60_plus"] = neighbourhood_insights.get("age60Plus", "")
                    item["long_term_resident"] = neighbourhood_insights.get(
                        "longTermResident", ""
                    )
                    item["owner_percentage"] = neighbourhood_insights.get("owner", "")
                    item["renter_percentage"] = neighbourhood_insights.get("renter", "")
                    item["family_percentage"] = neighbourhood_insights.get("family", "")
                    item["single_percentage"] = neighbourhood_insights.get("single", "")

                # Domain insights
                domain_says = component_props.get("domainSays", {})
                if domain_says:
                    item["first_listed_date"] = domain_says.get("firstListedDate", "")
                    item["last_sold_date"] = domain_says.get("lastSoldOnDate", "")
                    item["updated_date"] = domain_says.get("updatedDate", "")
                    item["number_sold"] = domain_says.get("numberSold", "")

                # Gallery information - use Selenium directly
                item["image_urls"] = self._extract_image_urls_with_selenium(
                    response.url
                )
                item["number_of_photos"] = len(item["image_urls"])

                # Inspection information
                inspection = component_props.get("inspection", {})
                if inspection:
                    item["inspection_text"] = inspection.get("inspectionText", "")
                    item["appointment_only"] = inspection.get("appointmentOnly", "")

                self.logger.info(
                    "Successfully extracted detailed property data from JSON"
                )

        except Exception as e:
            self.logger.error(f"Error extracting JSON data: {str(e)}")

    def _extract_image_urls_with_selenium(self, url):
        """Extract image URLs using Selenium by triggering the photo modal"""
        try:
            # Initialize driver if not already done
            self._init_selenium_driver()
            if not self.driver:
                self.logger.warning(
                    "Selenium driver not available for image extraction"
                )
                return []

            # Navigate to the page
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Check for specific selectors that might work
            selectors_to_try = [
                'button[aria-label="Launch Photos"]',
                'button[aria-label="Launch photos"]',
                'button[aria-label="launch photos"]',
                'button[aria-label*="Photos"]',
                'button[aria-label*="photos"]',
                'button[data-testid*="photo"]',
                'button[data-testid*="gallery"]',
                'button[class*="photo"]',
                'button[class*="gallery"]',
                'button[class*="image"]',
            ]

            working_selector = None
            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    working_selector = selector
                    break

            if not working_selector:
                return []

            # Try to click the button
            try:
                launch_photos_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, working_selector))
                )
                launch_photos_button.click()

                # Wait for the modal to open (look for common modal selectors)
                modal_selectors = [
                    ".pswp",  # PhotoSwipe modal
                    "[class*='modal']",
                    "[class*='gallery']",
                    "[class*='photo']",
                    "[data-testid*='modal']",
                    "[data-testid*='gallery']",
                ]

                modal_found = False
                for selector in modal_selectors:
                    try:
                        WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        modal_found = True
                        break
                    except:
                        continue

                if not modal_found:
                    return []

                # Wait a bit more for images to load
                import time

                time.sleep(2)

                # Try multiple selectors for images
                image_selectors = [
                    "img.pswp_img",
                    ".pswp img",
                    "[class*='pswp'] img",
                    "img[src*='domain']",
                    "img[src*='photo']",
                    "img[src*='image']",
                ]

                image_elements = []
                for selector in image_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        image_elements = elements
                        break

                if not image_elements:
                    return []
                image_urls = []

                for img in image_elements:
                    src = img.get_attribute("src")
                    if src and src not in image_urls:
                        image_urls.append(src)

                return image_urls

            except Exception as e:
                return []

        except Exception as e:
            return []

    def _extract_listing_card_features(self, listing_li):
        """Extract property features from listing card on search results page"""
        try:
            # Look for the listing card features wrapper
            features_wrapper = listing_li.css(
                'div[data-testid="listing-card-features-wrapper"]'
            )

            if features_wrapper:
                # Look for property features within the card
                property_features_div = features_wrapper.css(
                    'div[data-testid="property-features"]'
                )

                if property_features_div:
                    # Get all spans with property-features-text-container
                    feature_spans = property_features_div.css(
                        'span[data-testid="property-features-text-container"]::text'
                    ).getall()

                return ",".join(feature_spans)

            else:
                return ""

        except Exception as e:
            return ""

    def parse(self, response):
        """
        Parse the search results page and extract property listings
        Handles suburb-based scraping with dynamic page limits
        """
        try:
            suburb = response.meta.get("suburb", "Unknown")
            postcode = response.meta.get("postcode", "Unknown")
            page_number = response.meta.get("page_number", 1)
            suburb_url_base = response.meta.get("suburb_url_base", "")

            # Update progress tracking
            if self.current_suburb != suburb or self.current_postcode != postcode:
                self.current_suburb = suburb
                self.current_postcode = postcode
                self.current_page = 0
                self.total_listings = 0

            self.current_page = page_number

            # Show progress with tqdm
            progress_msg = f"Scraping {suburb} ({postcode}) - Page {page_number}"
            tqdm.write(progress_msg)

            self.logger.info(
                f"=== PARSING {suburb} ({postcode}) - PAGE {page_number} ==="
            )
            self.logger.info(f"URL: {response.url}")
            self.logger.info(f"Status Code: {response.status}")
            self.logger.info(f"Response Length: {len(response.body)} bytes")

            # Check if we got a valid response
            if response.status != 200:
                self.logger.error(f"Non-200 status code: {response.status}")
                return

            # Check for "No exact matches" - indicates no more listings
            no_matches = response.css('text:contains("No exact matches")').get()
            if no_matches:
                self.logger.info(
                    f"No more listings found for {suburb} ({postcode}) on page {page_number}"
                )
                self._log_suburb_stats(suburb, postcode, page_number - 1)
                return

            # Check if response is empty
            if len(response.body) < 1000:
                self.logger.warning(
                    f"Response seems too short: {len(response.body)} bytes"
                )
                return

            # Find the results ul element
            self.logger.info("Looking for ul element with data-testid='results'...")
            results_ul = response.css('ul[data-testid="results"]')
            self.logger.info(
                f"Found {len(results_ul)} ul elements with data-testid='results'"
            )

            if not results_ul:
                self.logger.warning(
                    f"No results ul element found for {suburb} on page {page_number}"
                )
                return

            # Find all li elements that are actual listings (not ads)
            listing_items = results_ul.css('li[data-testid^="listing-"]')
            self.logger.info(
                f"Found {len(listing_items)} property listings for {suburb} on page {page_number}"
            )

            # Update suburb stats
            if suburb not in self.suburb_stats:
                self.suburb_stats[suburb] = {
                    "postcode": postcode,
                    "total_listings": 0,
                    "pages_scraped": 0,
                }

            self.suburb_stats[suburb]["total_listings"] += len(listing_items)
            self.suburb_stats[suburb]["pages_scraped"] = page_number

            # Extract information from each listing
            for i, li in enumerate(listing_items):
                # Extract property features from listing card
                property_features = self._extract_listing_card_features(li)

                # Extract the listing link
                listing_link = (
                    li.css("a")
                    .xpath('.//h2[@data-testid="address-wrapper"]/parent::a/@href')
                    .get()
                )
                if listing_link:
                    # Make absolute URL
                    if listing_link.startswith("/"):
                        listing_url = f"https://www.domain.com.au{listing_link}"
                    else:
                        listing_url = listing_link

                    # Create a request to scrape the individual listing page
                    yield scrapy.Request(
                        url=listing_url,
                        callback=self.scrape_listing,
                        meta={
                            "suburb": suburb,
                            "postcode": postcode,
                            "page_number": page_number,
                            "listing_index": i + 1,
                            "property_features": property_features,
                        },
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                        },
                    )
                else:
                    pass

            # Generate request for next page if we found listings and haven't reached max pages
            if len(listing_items) > 0 and page_number < 50:
                next_page = page_number + 1
                next_url = f"{suburb_url_base}&page={next_page}"

                self.logger.info(f"Generating request for next page: {next_url}")

                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        "suburb": suburb,
                        "postcode": postcode,
                        "page_number": next_page,
                        "suburb_url_base": suburb_url_base,
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    },
                )
            elif len(listing_items) == 0:
                self.logger.info(
                    f"No listings found for {suburb} on page {page_number} - stopping pagination"
                )
                self._log_suburb_stats(suburb, postcode, page_number - 1)

            self.logger.info(f"=== FINISHED PARSING {suburb} PAGE {page_number} ===")

        except Exception as e:
            self.logger.error(
                f"Error parsing page {page_number} for {suburb}: {str(e)}"
            )
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return

    def _log_suburb_stats(self, suburb, postcode, final_page):
        """Log statistics for a suburb when scraping is complete"""
        if suburb in self.suburb_stats:
            stats = self.suburb_stats[suburb]
            self.logger.info(f"=== {suburb} ({postcode}) COMPLETE ===")
            self.logger.info(f"Total listings found: {stats['total_listings']}")
            self.logger.info(f"Pages scraped: {final_page}")
            self.logger.info(
                f"Average listings per page: {stats['total_listings'] / final_page if final_page > 0 else 0:.2f}"
            )
        else:
            self.logger.info(
                f"=== {suburb} ({postcode}) COMPLETE - No listings found ==="
            )
