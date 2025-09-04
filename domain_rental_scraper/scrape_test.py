import requests
from bs4 import BeautifulSoup
import time
import json

# Use the working headers from debug_connection.py
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

url = "https://www.domain.com.au"
num_pages = 50

# Initialize list to store all listings from all pages
all_listings = []


# Start timing
start_time = time.time()
print(f"🚀 Starting to fetch listings at {time.strftime('%Y-%m-%d %H:%M:%S')}")

for page in range(1, num_pages + 1):
    try:
        # print headers
        print(f"Headers: {headers}")
        page_url = f"{url}/rent/?sort=price-asc&page={page}"
        print(f"Fetching: {page_url}")

        response = requests.get(page_url, headers=headers, timeout=15, verify=True)
        response.raise_for_status()  # Raises an exception for bad status codes

        print(f"Status code: {response.status_code}")

        # Parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the results ul element
        results_ul = soup.find("ul", {"data-testid": "results"})

        if not results_ul:
            print("No results ul element found")
            break

        # Find all li elements that are actual listings (not ads)
        listing_items = results_ul.find_all(
            "li", {"data-testid": lambda x: x and x.startswith("listing-")}
        )

        print(f"Found {len(listing_items)} property listings on page {page}")

        # Extract information from each listing
        page_listings = []

        for li in listing_items:
            listing_data = {}

            # Extract listing title (price)
            price_p = li.find("p", {"data-testid": "listing-card-price"})
            if price_p:
                listing_data["listing_title"] = price_p.get_text().strip()
            else:
                listing_data["listing_title"] = ""

            # Extract address information
            address_wrapper = li.find("h2", {"data-testid": "address-wrapper"})
            if address_wrapper:
                # Address line 1
                address_line1 = address_wrapper.find(
                    "span", {"data-testid": "address-line1"}
                )
                listing_data["address_line_1"] = (
                    address_line1.get_text().strip() if address_line1 else ""
                )

                # Address line 2 (suburb, state, postcode)
                address_line2 = address_wrapper.find(
                    "span", {"data-testid": "address-line2"}
                )
                if address_line2:
                    spans = address_line2.find_all("span")
                    listing_data["suburb"] = (
                        spans[0].get_text().strip() if len(spans) > 0 else ""
                    )
                    listing_data["state"] = (
                        spans[1].get_text().strip() if len(spans) > 1 else ""
                    )
                    listing_data["postcode"] = (
                        spans[2].get_text().strip() if len(spans) > 2 else ""
                    )
                else:
                    listing_data["suburb"] = ""
                    listing_data["state"] = ""
                    listing_data["postcode"] = ""
            else:
                listing_data["address_line_1"] = ""
                listing_data["suburb"] = ""
                listing_data["state"] = ""
                listing_data["postcode"] = ""

            # Extract property features and type
            features_wrapper = li.find(
                "div", {"data-testid": "listing-card-features-wrapper"}
            )
            if features_wrapper:
                # Check if there are two div children
                div_children = features_wrapper.find_all("div", recursive=False)

                if len(div_children) >= 2:
                    # First div: property features
                    property_features_div = div_children[0]
                    if property_features_div.get("data-testid") == "property-features":
                        feature_spans = property_features_div.find_all(
                            "span", {"data-testid": "property-features-text-container"}
                        )
                        if len(feature_spans) >= 3:
                            features = [
                                span.get_text().strip() for span in feature_spans
                            ]
                            listing_data["property_features"] = ", ".join(features)
                        else:
                            listing_data["property_features"] = ""
                    else:
                        listing_data["property_features"] = ""

                    # Second div: property type
                    property_type_div = div_children[1]
                    property_type_span = property_type_div.find("span")
                    listing_data["property_type"] = (
                        property_type_span.get_text().strip()
                        if property_type_span
                        else ""
                    )
                else:
                    # Only one child div, set property_features to empty string
                    listing_data["property_features"] = ""
                    if len(div_children) == 1:
                        property_type_span = div_children[0].find("span")
                        listing_data["property_type"] = (
                            property_type_span.get_text().strip()
                            if property_type_span
                            else ""
                        )
                    else:
                        listing_data["property_type"] = ""
            else:
                listing_data["property_features"] = ""
                listing_data["property_type"] = ""

            page_listings.append(listing_data)

        # Add page listings to the overall list
        all_listings.extend(page_listings)

        print(f"Added {len(page_listings)} listings from page {page}")
        print(f"Total listings collected so far: {len(all_listings)}")

        # Print the extracted information for this page as JSON
        print(f"\nListings from page {page}:")
        print(json.dumps(page_listings, indent=2))

        # Save the HTML body content to a file for inspection (only for first page)
        if page == 1:
            with open("scrape_test.html", "w", encoding="utf-8") as f:
                f.write(soup.body.prettify())
            print("Saved HTML content to 'scrape_test.html' for inspection")

        # Add delay between requests to avoid rate limiting
        time.sleep(1)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        continue
    except Exception as e:
        print(f"Unexpected error on page {page}: {e}")
        continue

# Calculate total time
end_time = time.time()
total_duration = end_time - start_time

# Print all collected listings
print(f"\n=== ALL LISTINGS COLLECTED ===")
print(f"Total listings: {len(all_listings)}")
print(f"⏱️  Total time taken: {total_duration:.2f} seconds")
print(
    f"⏱️  Average time per page: {total_duration/len(all_listings) if all_listings else 0:.2f} seconds"
)
print(
    f"⏱️  Average time per listing: {total_duration/len(all_listings) if all_listings else 0:.2f} seconds"
)
print(json.dumps(all_listings, indent=2))

# Save all listings to a JSON file
with open("domain_rental_listings.json", "w", encoding="utf-8") as f:
    json.dump(all_listings, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(all_listings)} listings to 'domain_rental_listings.json'")
print(f"✅ Test completed successfully! Total time: {total_duration:.2f} seconds")
