#!/usr/bin/env python3
"""
Wayback Machine Domain.com.au Spider

This spider is specifically designed to scrape Domain.com.au rental listings
from Wayback Machine archives (2022-2024) which have a different HTML structure
than the current website.

The spider extracts data from the __NEXT_DATA__ JSON structure embedded in the HTML.
"""

import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from domain_scraper.items import DomainScraperItem


class WaybackDomainSpider(scrapy.Spider):
    name = "wayback_domain_rental"

    def __init__(
        self,
        wayback_timestamp=None,
        target_suburb=None,
        target_postcode=None,
        output_file=None,
        *args,
        **kwargs,
    ):
        super().__init__()
        self.suburb_data = self._load_suburb_data()
        self.suburb_stats = {}  # Track listings per suburb
        self.suburb_timings = {}  # Track timing for each suburb
        self.current_suburb = None
        self.current_postcode = None
        self.current_page = 0
        self.total_listings = 0
        self.wayback_timestamp = wayback_timestamp
        self.target_suburb = target_suburb
        self.target_postcode = target_postcode
        self.output_file = output_file

        # Log the wayback timestamp being used
        if self.wayback_timestamp:
            self.logger.info(f"🕐 Using Wayback timestamp: {self.wayback_timestamp}")
        else:
            self.logger.info("🌐 Scraping current domain.com.au (no Wayback timestamp)")

        # Log target suburb if specified
        if self.target_suburb and self.target_postcode:
            self.logger.info(
                f"🎯 Target suburb: {self.target_suburb} ({self.target_postcode})"
            )
        else:
            self.logger.info("🌍 Scraping all suburbs")

    def _load_suburb_data(self):
        """Load suburb data from CSV file"""
        import pandas as pd
        import os

        # Try different possible paths for the CSV file
        possible_paths = [
            "data/snapshots/suburb_snapshots_2022_2025_quarterly_snapshots.csv",
            "../../data/snapshots/suburb_snapshots_2022_2025_quarterly_snapshots.csv",
            "../data/snapshots/suburb_snapshots_2022_2025_quarterly_snapshots.csv",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"DEBUG: Found CSV file at: {path}")
                return pd.read_csv(path)

        # If no CSV found, return empty DataFrame
        print("WARNING: No suburb data CSV found, using empty DataFrame")
        return pd.DataFrame()

    def start_requests(self):
        """Generate initial requests for each suburb"""
        import pandas as pd

        if self.wayback_timestamp:
            # Use the provided timestamp for all requests
            actual_timestamp = str(int(float(self.wayback_timestamp)))

            if self.target_suburb and self.target_postcode:
                # Filter for specific suburb
                filtered_data = self.suburb_data[
                    (
                        self.suburb_data["suburb"].str.lower()
                        == self.target_suburb.lower()
                    )
                    & (self.suburb_data["postcode"] == int(self.target_postcode))
                ]
                self.logger.info(f"Filtered data shape: {filtered_data.shape}")
                self.logger.info(
                    f"Target suburb: {self.target_suburb}, postcode: {self.target_postcode}"
                )
            else:
                # Use all suburbs
                filtered_data = self.suburb_data

            for _, row in filtered_data.iterrows():
                suburb = row["suburb"]
                postcode = row["postcode"]

                # Create wayback URL
                wayback_url = f"https://web.archive.org/web/{actual_timestamp}/https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}/"

                yield scrapy.Request(
                    url=wayback_url,
                    callback=self.parse,
                    meta={
                        "suburb": suburb,
                        "postcode": postcode,
                        "actual_timestamp": actual_timestamp,
                    },
                )
        else:
            # Fallback to current domain.com.au if no timestamp provided
            self.logger.warning(
                "No wayback timestamp provided, this spider requires a timestamp"
            )

    def parse(self, response):
        """Parse the search results page"""
        suburb = response.meta.get("suburb", "Unknown")
        postcode = response.meta.get("postcode", "Unknown")
        actual_timestamp = response.meta.get("actual_timestamp", "")
        page_number = response.meta.get("page_number", 1)

        self.logger.info(f"🔍 Parsing {suburb} ({postcode}) - Page {page_number}")

        # Extract listings from __NEXT_DATA__ JSON
        listings = self._extract_listings_from_json(response)

        if not listings:
            self.logger.warning(f"No listings found for {suburb} ({postcode})")
            return

        self.logger.info(f"📊 Found {len(listings)} listings for {suburb} ({postcode})")

        # Process each listing
        for i, listing_data in enumerate(listings):
            # Create comprehensive item from JSON data
            item = self._create_comprehensive_item_from_json(
                listing_data, actual_timestamp, suburb, postcode
            )
            if item:
                yield item

        # Check for pagination
        self._handle_pagination(response, suburb, postcode, actual_timestamp)

    def _extract_listings_from_json(self, response):
        """Extract listings from __NEXT_DATA__ JSON structure"""
        try:
            # Look for __NEXT_DATA__ script tag
            script_content = response.css("script#__NEXT_DATA__::text").get()
            if not script_content:
                self.logger.warning("No __NEXT_DATA__ script found")
                return []

            data = json.loads(script_content)

            # Debug: Print the top-level structure
            self.logger.info(f"JSON top-level keys: {list(data.keys())}")

            # Navigate through the JSON structure to find listings
            # The structure may vary, so we try multiple possible paths
            listings = []

            # Try different possible paths for listings
            possible_paths = [
                data.get("props", {})
                .get("pageProps", {})
                .get("componentProps", {})
                .get("listingsMap", {}),
                data.get("props", {}).get("pageProps", {}).get("listingsMap", {}),
                data.get("props", {}).get("listingsMap", {}),
                data.get("listingsMap", {}),
            ]

            for i, path in enumerate(possible_paths):
                if path and isinstance(path, dict):
                    # Extract listings from the map
                    listings = list(path.values())
                    if listings:
                        self.logger.info(
                            f"Found {len(listings)} listings in JSON structure using path {i}"
                        )
                        # Debug: Print a sample listing structure
                        if listings:
                            sample = listings[0]
                            self.logger.info(
                                f"Sample listing keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}"
                            )
                        break

            if not listings:
                self.logger.warning("No listings found in any expected JSON path")
                # Debug: print the structure of the JSON
                self.logger.info(f"JSON structure keys: {list(data.keys())}")
                if "props" in data:
                    self.logger.info(f"Props keys: {list(data['props'].keys())}")
                    if "pageProps" in data["props"]:
                        self.logger.info(
                            f"PageProps keys: {list(data['props']['pageProps'].keys())}"
                        )
                return []

            return listings

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse __NEXT_DATA__ JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting listings from JSON: {e}")
            return []

    def _create_comprehensive_item_from_json(
        self, listing_data, actual_timestamp, suburb, postcode
    ):
        """Create a simplified DomainScraperItem with only relevant columns that have data"""
        try:
            if not isinstance(listing_data, dict):
                return None

            item = DomainScraperItem()

            # Extract data from the correct JSON structure
            # Basic property information
            item["property_id"] = listing_data.get("id", "")

            # Get listing model data
            listing_model = listing_data.get("listingModel", {})
            item["url"] = listing_model.get("url", "")
            item["rental_price"] = listing_model.get("price", "")

            # Property features from listingModel.features
            features = listing_model.get("features", {})
            item["bedrooms"] = features.get("beds", "")
            item["bathrooms"] = features.get("baths", "")
            item["car_spaces"] = features.get("parking", "")
            item["property_type"] = features.get("propertyTypeFormatted", "")
            item["land_area"] = features.get("landSize", "")

            # Property features as a structured string (this format appears in the data)
            property_features_str = f"{features.get('beds', '')}, ,{features.get('baths', '')}, ,{features.get('parking', '')},"
            if features.get("landSize"):
                property_features_str += f" {features.get('landSize')},"
            item["property_features"] = property_features_str

            # Address information
            address = listing_model.get("address", {})
            item["suburb"] = address.get("suburb", suburb)
            item["postcode"] = address.get("postcode", postcode)

            # Set scraped_date from wayback timestamp (proper format)
            if actual_timestamp:
                try:
                    # Convert timestamp string to datetime
                    dt = datetime.strptime(actual_timestamp, "%Y%m%d%H%M%S")
                    item["scraped_date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    item["scraped_date"] = actual_timestamp
            else:
                item["scraped_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Set wayback-specific fields
            item["wayback_url"] = (
                f"https://web.archive.org/web/{actual_timestamp}/https://www.domain.com.au{item['url']}"
                if actual_timestamp and item["url"]
                else ""
            )
            item["wayback_time"] = actual_timestamp or ""

            # Set all other fields to empty strings to maintain consistent structure
            for field in item.fields:
                if field not in [
                    "property_id",
                    "url",
                    "rental_price",
                    "bedrooms",
                    "bathrooms",
                    "car_spaces",
                    "property_type",
                    "land_area",
                    "property_features",
                    "suburb",
                    "postcode",
                    "scraped_date",
                    "wayback_url",
                    "wayback_time",
                ]:
                    item[field] = ""

            return item

        except Exception as e:
            self.logger.error(f"Error creating item from JSON: {e}")
            return None

    def _handle_pagination(self, response, suburb, postcode, actual_timestamp):
        """Handle pagination by extracting totalPages from JSON"""
        try:
            script_content = response.css("script#__NEXT_DATA__::text").get()
            if not script_content:
                return

            data = json.loads(script_content)

            # Try to find totalPages in the JSON structure
            total_pages = None
            possible_paths = [
                data.get("props", {})
                .get("pageProps", {})
                .get("componentProps", {})
                .get("totalPages"),
                data.get("props", {}).get("pageProps", {}).get("totalPages"),
                data.get("props", {}).get("totalPages"),
                data.get("totalPages"),
            ]

            for path in possible_paths:
                if path is not None:
                    total_pages = int(path)
                    break

            if total_pages and total_pages > 1:
                current_page = response.meta.get("page_number", 1)

                if current_page < total_pages:
                    next_page = current_page + 1
                    next_url = f"https://web.archive.org/web/{actual_timestamp}/https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}/?page={next_page}"

                    self.logger.info(
                        f"📄 Following pagination to page {next_page} for {suburb}"
                    )

                    yield scrapy.Request(
                        url=next_url,
                        callback=self.parse,
                        meta={
                            "suburb": suburb,
                            "postcode": postcode,
                            "actual_timestamp": actual_timestamp,
                            "page_number": next_page,
                        },
                        errback=self.handle_error,
                    )
            else:
                self.logger.info(f"📄 No pagination found for {suburb}")

        except Exception as e:
            self.logger.error(f"❌ Error handling pagination: {e}")

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"❌ Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")

    def _log_suburb_completion(self):
        """Log completion statistics for the current suburb"""
        if self.current_suburb:
            self.logger.info(
                f"✅ Completed {self.current_suburb} ({self.current_postcode}) - "
                f"Total listings: {self.total_listings}"
            )
