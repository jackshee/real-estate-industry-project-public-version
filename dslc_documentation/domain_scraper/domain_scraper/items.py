# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DomainScraperItem(scrapy.Item):
    # Property listing data fields
    property_features = scrapy.Field()  # Comma-delimited property features
    property_type = scrapy.Field()  # Property type (house, apartment, etc.)
    url = scrapy.Field()  # URL of the listing page

    # Address details
    full_address = scrapy.Field()  # Complete address
    unit_number = scrapy.Field()  # Unit/apartment number
    street_number = scrapy.Field()  # Street number
    street = scrapy.Field()  # Street name
    state_abbreviation = scrapy.Field()  # State abbreviation

    # Property identification
    property_id = scrapy.Field()  # Unique property identifier
    listing_url = scrapy.Field()  # Full listing URL

    # Agent and agency information
    agent_name = scrapy.Field()  # Real estate agent name
    agency_name = scrapy.Field()  # Agency name

    # Property details
    description = scrapy.Field()  # Property description
    features_list = scrapy.Field()  # List of features
    structured_features = scrapy.Field()  # Structured feature data

    # Price and status information
    rental_price = scrapy.Field()  # Rental price
    listing_status = scrapy.Field()  # Listing status
    listing_tag = scrapy.Field()  # Listing tag

    # Location data
    latitude = scrapy.Field()  # Property latitude
    longitude = scrapy.Field()  # Property longitude

    # Market insights
    median_rent_price = scrapy.Field()  # Median rent in suburb
    median_sold_price = scrapy.Field()  # Median sold price in suburb
    avg_days_on_market = scrapy.Field()  # Average days on market
    renter_percentage = scrapy.Field()  # Percentage of renters in suburb
    single_percentage = scrapy.Field()  # Percentage of single households

    # Neighbourhood demographics
    age_0_to_19 = scrapy.Field()  # Age group 0-19 percentage
    age_20_to_39 = scrapy.Field()  # Age group 20-39 percentage
    age_40_to_59 = scrapy.Field()  # Age group 40-59 percentage
    age_60_plus = scrapy.Field()  # Age group 60+ percentage
    long_term_resident = scrapy.Field()  # Long-term resident percentage
    owner_percentage = scrapy.Field()  # Owner-occupier percentage
    renter_percentage = scrapy.Field()  # Renter percentage
    family_percentage = scrapy.Field()  # Family household percentage
    single_percentage = scrapy.Field()  # Single household percentage

    # Domain insights
    first_listed_date = scrapy.Field()  # First listed date
    last_sold_date = scrapy.Field()  # Last sold date
    updated_date = scrapy.Field()  # Last updated date
    number_sold = scrapy.Field()  # Number of properties sold in area

    # Media and inspection
    number_of_photos = scrapy.Field()  # Number of photos
    image_urls = scrapy.Field()  # List of image URLs
    inspection_text = scrapy.Field()  # Inspection text
    appointment_only = scrapy.Field()  # Appointment only flag

    # School information
    schools = (
        scrapy.Field()
    )  # List of tuples: (school_name, school_type, school_level, distance)

    # Scraping metadata
    suburb = scrapy.Field()  # Suburb used for scraping (from CSV)
    postcode = scrapy.Field()  # Postcode used for scraping (from CSV)
