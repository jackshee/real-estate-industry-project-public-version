#!/usr/bin/env python3
"""
Analyze Domain.com.au listing page data to identify features useful for rental price prediction
"""

import json
import re
from collections import Counter

def analyze_listing_data():
    """Analyze the listing data and create a markdown report"""
    
    # Load the JSON data
    with open('listing_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract property information
    props = data.get('props', {})
    page_props = props.get('pageProps', {})
    
    print("# Domain.com.au Listing Page Analysis")
    print("## Property Details Found")
    print()
    
    # Extract basic property info
    layout_props = page_props.get('layoutProps', {})
    title = layout_props.get('title', '')
    description = layout_props.get('description', '')
    
    print(f"**Title:** {title}")
    print(f"**Description:** {description}")
    print()
    
    # Look for property features in the description
    bedroom_match = re.search(r'(\d+)\s+bedroom', description, re.IGNORECASE)
    bathroom_match = re.search(r'(\d+)\s+bathroom', description, re.IGNORECASE)
    
    if bedroom_match:
        print(f"**Bedrooms:** {bedroom_match.group(1)}")
    if bathroom_match:
        print(f"**Bathrooms:** {bathroom_match.group(1)}")
    
    print()
    
    # Analyze the full data structure
    print("## Data Structure Analysis")
    print()
    
    def analyze_structure(obj, path="", max_depth=3, current_depth=0):
        """Recursively analyze the data structure"""
        if current_depth >= max_depth:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)) and value:
                    print(f"- **{new_path}**: {type(value).__name__} with {len(value)} items")
                    if current_depth < max_depth - 1:
                        analyze_structure(value, new_path, max_depth, current_depth + 1)
                else:
                    if isinstance(value, str) and len(value) > 100:
                        print(f"- **{new_path}**: {type(value).__name__} (long text: {value[:100]}...)")
                    else:
                        print(f"- **{new_path}**: {type(value).__name__} = {value}")
        elif isinstance(obj, list):
            print(f"- **{path}**: List with {len(obj)} items")
            if obj and current_depth < max_depth - 1:
                analyze_structure(obj[0], f"{path}[0]", max_depth, current_depth + 1)
    
    analyze_structure(page_props)
    
    print()
    print("## Features Relevant for Rental Price Prediction")
    print()
    
    # Look for specific property features that would be useful for price prediction
    relevant_features = [
        "bedrooms", "bathrooms", "parking", "garage", "car space",
        "property_type", "building_type", "land_size", "floor_area",
        "year_built", "age", "condition", "furnished", "unfurnished",
        "balcony", "garden", "pool", "gym", "elevator", "air_conditioning",
        "heating", "dishwasher", "laundry", "study", "storage",
        "suburb", "postcode", "state", "distance_to_city", "distance_to_transport",
        "schools_nearby", "shopping_nearby", "amenities", "crime_rate",
        "rental_yield", "capital_growth", "demand", "supply"
    ]
    
    print("### High-Impact Features (Strongly Correlated with Price):")
    high_impact = [
        "**Bedrooms** - Number of bedrooms (most important factor)",
        "**Bathrooms** - Number of bathrooms",
        "**Property Type** - House, Apartment, Unit, Townhouse, etc.",
        "**Location** - Suburb, postcode, distance to city center",
        "**Parking** - Number of car spaces/garage",
        "**Floor Area** - Size of the property in square meters"
    ]
    for feature in high_impact:
        print(f"- {feature}")
    
    print()
    print("### Medium-Impact Features (Moderately Correlated with Price):")
    medium_impact = [
        "**Year Built** - Age of the property",
        "**Condition** - New, renovated, needs work, etc.",
        "**Amenities** - Pool, gym, balcony, garden, etc.",
        "**Furnished Status** - Fully furnished, partially furnished, unfurnished",
        "**Building Features** - Elevator, air conditioning, heating, etc.",
        "**Outdoor Space** - Balcony, garden, courtyard size"
    ]
    for feature in medium_impact:
        print(f"- {feature}")
    
    print()
    print("### Location-Based Features (Context-Dependent):")
    location_features = [
        "**Distance to CBD** - Proximity to city center",
        "**Public Transport** - Distance to train/bus stops",
        "**Schools** - Quality and proximity of nearby schools",
        "**Shopping** - Distance to shopping centers",
        "**Crime Rate** - Safety of the area",
        "**Demographics** - Age profile, income levels of residents"
    ]
    for feature in location_features:
        print(f"- {feature}")
    
    print()
    print("### Market Features (External Factors):")
    market_features = [
        "**Rental Yield** - Historical rental returns in the area",
        "**Capital Growth** - Property value appreciation trends",
        "**Supply/Demand** - Number of available properties vs. demand",
        "**Seasonal Factors** - Time of year, market conditions",
        "**Agent/Listing Quality** - Professional presentation, photos, etc."
    ]
    for feature in market_features:
        print(f"- {feature}")
    
    print()
    print("## Data Extraction Recommendations")
    print()
    print("Based on the analysis, the following data should be prioritized for extraction:")
    print()
    print("### 1. Core Property Features")
    print("- Bedrooms (number)")
    print("- Bathrooms (number)")
    print("- Parking spaces (number)")
    print("- Property type (house, apartment, etc.)")
    print("- Floor area (square meters)")
    print("- Year built/age")
    print()
    print("### 2. Location Data")
    print("- Full address (street, suburb, state, postcode)")
    print("- Distance to CBD (if available)")
    print("- Distance to nearest train station")
    print("- School catchment areas")
    print()
    print("### 3. Property Condition & Amenities")
    print("- Furnished status")
    print("- Air conditioning")
    print("- Heating")
    print("- Balcony/outdoor space")
    print("- Garden/yard")
    print("- Pool")
    print("- Gym/fitness facilities")
    print()
    print("### 4. Market Context")
    print("- Days on market")
    print("- Price history (if available)")
    print("- Similar properties in area")
    print("- Rental yield data")
    print()
    print("### 5. Agent/Listing Quality")
    print("- Number of photos")
    print("- Quality of description")
    print("- Agent experience/rating")
    print("- Inspection availability")
    
    print()
    print("## Implementation Notes")
    print()
    print("1. **Data Quality**: Ensure consistent data types (numbers for bedrooms, bathrooms, etc.)")
    print("2. **Missing Data**: Handle missing values appropriately (imputation vs. exclusion)")
    print("3. **Feature Engineering**: Create derived features like 'price_per_sqm', 'bedroom_bathroom_ratio'")
    print("4. **Location Encoding**: Use postcode or suburb as categorical features, or geocode to lat/lng")
    print("5. **Text Features**: Extract keywords from descriptions for amenities and condition")
    print("6. **Temporal Features**: Consider seasonality and market timing")
    
    print()
    print("## Next Steps")
    print()
    print("1. Update the spider to extract these additional features")
    print("2. Implement data validation and cleaning pipelines")
    print("3. Create feature engineering functions")
    print("4. Build a comprehensive dataset for price prediction modeling")

if __name__ == "__main__":
    analyze_listing_data()
