# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DomainScraperItem(scrapy.Item):
    # Property listing data fields matching scrape_test.py structure
    listing_title = scrapy.Field()  # Price/title from listing-card-price
    address_line_1 = scrapy.Field()  # First line of address
    suburb = scrapy.Field()  # Suburb from address-line2
    state = scrapy.Field()  # State from address-line2
    postcode = scrapy.Field()  # Postcode from address-line2
    property_features = scrapy.Field()  # Comma-delimited property features
    property_type = scrapy.Field()  # Property type (house, apartment, etc.)
    page_number = scrapy.Field()  # Which page this listing was found on
    url = scrapy.Field()  # URL of the listing page
