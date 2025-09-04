# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import logging
from itemadapter import ItemAdapter


class DomainScraperPipeline:
    """
    Pipeline to process and clean scraped property data
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_count = 0

    def process_item(self, item, spider):
        """
        Process and clean each scraped item
        """
        adapter = ItemAdapter(item)

        # Clean and validate data
        self._clean_text_fields(adapter)
        self._validate_required_fields(adapter)

        self.processed_count += 1

        if self.processed_count % 10 == 0:
            self.logger.info(f"Processed {self.processed_count} items")

        return item

    def _clean_text_fields(self, adapter):
        """
        Clean text fields by stripping whitespace and handling None values
        """
        text_fields = [
            "listing_title",
            "address_line_1",
            "suburb",
            "state",
            "postcode",
            "property_features",
            "property_type",
        ]

        for field in text_fields:
            value = adapter.get(field)
            if value is not None:
                adapter[field] = str(value).strip()
            else:
                adapter[field] = ""

    def _validate_required_fields(self, adapter):
        """
        Validate that required fields are present
        """
        required_fields = ["listing_title", "address_line_1"]

        for field in required_fields:
            if not adapter.get(field):
                self.logger.warning(f"Missing required field '{field}' in item")

    def close_spider(self, spider):
        """
        Called when the spider closes
        """
        self.logger.info(f"Pipeline processed {self.processed_count} total items")


class JsonWriterPipeline:
    """
    Pipeline to write items to JSON file
    """

    def __init__(self):
        self.file = None
        self.items = []

    def open_spider(self, spider):
        """
        Open the JSON file when spider starts
        """
        self.file = open("domain_rental_listings.json", "w", encoding="utf-8")
        self.file.write("[\n")

    def close_spider(self, spider):
        """
        Close the JSON file when spider ends
        """
        if self.items:
            # Write the last item without a trailing comma
            self.file.write(json.dumps(self.items[-1], indent=2, ensure_ascii=False))

        self.file.write("\n]")
        self.file.close()

    def process_item(self, item, spider):
        """
        Process each item and write to JSON
        """
        if self.items:
            # Add comma after previous item
            self.file.write(",\n")
            self.file.write(json.dumps(dict(item), indent=2, ensure_ascii=False))
        else:
            # First item
            self.file.write(json.dumps(dict(item), indent=2, ensure_ascii=False))

        self.items.append(dict(item))
        return item
