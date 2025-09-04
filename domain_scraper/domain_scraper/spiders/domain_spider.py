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
from urllib.parse import urlparse, parse_qs
from ..items import DomainScraperItem


class DomainRentalSpider(scrapy.Spider):
    name = "domain_rental"
    allowed_domains = ["domain.com.au"]

    # Start with the first page
    start_urls = ["https://www.domain.com.au/rent/?sort=price-asc&page=1"]

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

    def start_requests(self):
        """Generate requests for multiple pages"""
        self.logger.info("=== STARTING REQUESTS GENERATION ===")

        # Generate URLs for pages 1-50 (or adjust as needed)
        # For testing, let's start with just 3 pages
        for page in range(1, 51):  # 3 pages for testing
            url = f"https://www.domain.com.au/rent/?sort=price-asc&page={page}"
            self.logger.info(f"Generating request for page {page}: {url}")

            request = scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"page_number": page},
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
            )

            self.logger.info(f"Request headers: {request.headers}")
            yield request

        self.logger.info("=== FINISHED REQUESTS GENERATION ===")

    def parse(self, response):
        """
        Parse the search results page and extract property listings
        Uses the same logic as scrape_test.py
        """
        try:
            page_number = response.meta.get("page_number", 1)
            self.logger.info(f"=== PARSING PAGE {page_number} ===")
            self.logger.info(f"URL: {response.url}")
            self.logger.info(f"Status Code: {response.status}")
            self.logger.info(f"Response Length: {len(response.body)} bytes")

            # Log response headers
            self.logger.info(f"Response Headers: {dict(response.headers)}")

            # Save response for debugging
            with open(
                f"scrapy_response_page_{page_number}.html", "w", encoding="utf-8"
            ) as f:
                f.write(response.text)
            self.logger.info(
                f"Saved response HTML to scrapy_response_page_{page_number}.html"
            )

            # Check if we got a valid response
            if response.status != 200:
                self.logger.error(f"Non-200 status code: {response.status}")
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
                    f"No results ul element found on page {page_number}"
                )
                # Try alternative selectors
                self.logger.info("Trying alternative selectors...")
                alt_results = response.css("ul")
                self.logger.info(f"Found {len(alt_results)} total ul elements")

                # Log all ul elements with their attributes
                for i, ul in enumerate(alt_results):
                    testid = ul.css("::attr(data-testid)").get()
                    self.logger.info(f"UL {i}: data-testid='{testid}'")

                return

            # Find all li elements that are actual listings (not ads)
            self.logger.info(
                "Looking for li elements with data-testid starting with 'listing-'..."
            )
            listing_items = results_ul.css('li[data-testid^="listing-"]')
            self.logger.info(
                f"Found {len(listing_items)} property listings on page {page_number}"
            )

            # Log all li elements in the results ul
            all_li_items = results_ul.css("li")
            self.logger.info(f"Total li elements in results ul: {len(all_li_items)}")

            for i, li in enumerate(all_li_items):
                testid = li.css("::attr(data-testid)").get()
                self.logger.info(f"LI {i}: data-testid='{testid}'")

            # Extract information from each listing
            for i, li in enumerate(listing_items):
                self.logger.info(f"--- PROCESSING LISTING {i+1} ---")
                item = DomainScraperItem()

                # Extract listing title (price)
                self.logger.info("Extracting listing title (price)...")
                price_p = li.css('p[data-testid="listing-card-price"]::text').get()
                item["listing_title"] = price_p.strip() if price_p else ""
                self.logger.info(f"Listing title: '{item['listing_title']}'")

                # Extract address information
                self.logger.info("Extracting address information...")
                address_wrapper = li.css('h2[data-testid="address-wrapper"]')
                self.logger.info(f"Found {len(address_wrapper)} address wrappers")

                if address_wrapper:
                    # Address line 1
                    address_line1 = address_wrapper.css(
                        'span[data-testid="address-line1"]::text'
                    ).get()
                    item["address_line_1"] = (
                        address_line1.strip() if address_line1 else ""
                    )
                    self.logger.info(f"Address line 1: '{item['address_line_1']}'")

                    # Address line 2 (suburb, state, postcode)
                    address_line2 = address_wrapper.css(
                        'span[data-testid="address-line2"]'
                    )
                    self.logger.info(
                        f"Found {len(address_line2)} address line 2 elements"
                    )

                    if address_line2:
                        spans = address_line2.css("span::text").getall()
                        self.logger.info(f"Address line 2 spans: {spans}")
                        item["suburb"] = spans[0].strip() if len(spans) > 0 else ""
                        item["state"] = spans[1].strip() if len(spans) > 1 else ""
                        item["postcode"] = spans[2].strip() if len(spans) > 2 else ""
                    else:
                        item["suburb"] = ""
                        item["state"] = ""
                        item["postcode"] = ""

                    self.logger.info(
                        f"Suburb: '{item['suburb']}', State: '{item['state']}', Postcode: '{item['postcode']}'"
                    )
                else:
                    item["address_line_1"] = ""
                    item["suburb"] = ""
                    item["state"] = ""
                    item["postcode"] = ""
                    self.logger.warning("No address wrapper found")

                # Extract property features and type
                self.logger.info("Extracting property features and type...")
                features_wrapper = li.css(
                    'div[data-testid="listing-card-features-wrapper"]'
                )
                self.logger.info(f"Found {len(features_wrapper)} features wrappers")

                if features_wrapper:
                    # Check if there are two div children (direct children only)
                    div_children = features_wrapper.xpath("./div")
                    self.logger.info(
                        f"Found {len(div_children)} div children in features wrapper"
                    )

                    if len(div_children) >= 2:
                        # First div: property features
                        property_features_div = div_children[0]
                        testid = property_features_div.css("::attr(data-testid)").get()
                        self.logger.info(f"First div data-testid: '{testid}'")

                        if testid == "property-features":
                            feature_spans = property_features_div.css(
                                'span[data-testid="property-features-text-container"]::text'
                            ).getall()
                            self.logger.info(f"Feature spans: {feature_spans}")

                            if len(feature_spans) >= 3:
                                features = [span.strip() for span in feature_spans]
                                item["property_features"] = ", ".join(features)
                            else:
                                item["property_features"] = ""
                        else:
                            item["property_features"] = ""

                        # Second div: property type
                        property_type_div = div_children[1]
                        property_type_span = property_type_div.css("span::text").get()
                        item["property_type"] = (
                            property_type_span.strip() if property_type_span else ""
                        )
                    else:
                        # Only one child div, set property_features to empty string
                        item["property_features"] = ""
                        if len(div_children) == 1:
                            property_type_span = div_children[0].css("span::text").get()
                            item["property_type"] = (
                                property_type_span.strip() if property_type_span else ""
                            )
                        else:
                            item["property_type"] = ""
                else:
                    item["property_features"] = ""
                    item["property_type"] = ""
                    self.logger.warning("No features wrapper found")

                self.logger.info(f"Property features: '{item['property_features']}'")
                self.logger.info(f"Property type: '{item['property_type']}'")

                # Add metadata
                item["page_number"] = page_number
                item["url"] = response.url

                self.logger.info(f"Yielding item: {dict(item)}")
                yield item

                self.logger.info(f"=== FINISHED PARSING PAGE {page_number} ===")

        except Exception as e:
            self.logger.error(f"Error parsing page {page_number}: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return
