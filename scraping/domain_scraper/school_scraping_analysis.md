# School Information Scraping Analysis

## Overview
This document explains how school information is extracted from Domain.com.au property listing pages for the purpose of rental price prediction.

## Data Location in HTML Structure

The school information is located in the `__NEXT_DATA__` JSON script tag within the HTML page. The data structure is:

```json
{
  "props": {
    "pageProps": {
      "componentProps": {
        "schoolCatchment": {
          "schools": [
            {
              "id": "3946",
              "educationLevel": "secondary",
              "name": "University High School",
              "distance": 2251.8512685711244,
              "state": "VIC",
              "postCode": "3052",
              "year": "7-12",
              "gender": "CoEd",
              "type": "Government",
              "address": "Parkville, VIC 3052",
              "url": "http://www.unihigh.vic.edu.au",
              "domainSeoUrlSlug": "university-high-school-vic-3052-3946",
              "status": "Open"
            }
          ],
          "numberOfVisibleSchools": 3,
          "enableSchoolProfileLink": true
        }
      }
    }
  }
}
```

## School Data Fields

Each school object contains the following fields:

- **`id`**: Unique school identifier (may be empty for some schools)
- **`educationLevel`**: School level - "primary", "secondary", "combined", or "childcare"
- **`name`**: School name
- **`distance`**: Distance from property in meters (as a float)
- **`state`**: State abbreviation (e.g., "VIC")
- **`postCode`**: School's postcode
- **`year`**: Year levels offered (e.g., "Prep-6", "7-12", "10-12")
- **`gender`**: Gender policy - "CoEd", "Boys", "Girls", or empty
- **`type`**: School type - "Government" or "Private"
- **`address`**: Full school address
- **`url`**: School website URL
- **`domainSeoUrlSlug`**: Domain's SEO-friendly URL slug for the school
- **`status`**: School status - "Open" or other statuses

## School Categories

Based on the `educationLevel` and `type` fields, schools can be categorized as:

1. **Primary Schools**: `educationLevel` = "primary" + `type` = "Government" or "Private"
2. **Secondary Schools**: `educationLevel` = "secondary" + `type` = "Government" or "Private"  
3. **Combined Schools**: `educationLevel` = "combined" + `type` = "Government" or "Private"
4. **Childcare**: `educationLevel` = "childcare" + `type` = "Government" or "Private"

## Implementation Strategy

The school information will be extracted as a list of tuples with the format:
```python
schools = [
    (school_name, school_type, school_level, distance_from_property),
    # ... more schools
]
```

Where:
- **`school_name`**: The `name` field from the JSON
- **`school_type`**: The `type` field ("Government" or "Private")
- **`school_level`**: The `educationLevel` field ("primary", "secondary", "combined", "childcare")
- **`distance_from_property`**: The `distance` field (in meters)

## Relevance for Rental Price Prediction

School information is highly relevant for rental price prediction because:

1. **Family Appeal**: Properties near good schools command higher rents
2. **School Quality**: Proximity to high-performing schools increases desirability
3. **Convenience**: Distance to schools affects daily commute and lifestyle
4. **School Type**: Private vs government schools may indicate different demographic preferences
5. **School Level**: Primary vs secondary schools affect different family life stages

## Data Quality Considerations

- Some schools may have empty `id` fields
- Distance is provided in meters as a float
- Not all properties will have school information available
- The `numberOfVisibleSchools` field indicates how many schools are shown by default
- Some schools may have `isRadiusResult: true` indicating they're within a search radius

## Example Output

For a property in Melbourne, the schools data might look like:

```python
schools = [
    ("Eltham College - Lonsdale Street Campus", "Private", "combined", 472.81),
    ("Ozford College - Ozford College Campus", "Private", "secondary", 952.32),
    ("Docklands Primary School", "Government", "primary", 1774.02),
    ("University High School", "Government", "secondary", 2251.85),
    ("Collingwood English Language School", "Government", "combined", 2302.28)
]
```

This data can be used to create features such as:
- Number of schools within 1km
- Distance to nearest primary school
- Distance to nearest secondary school
- Number of private vs government schools nearby
- Average distance to all schools



