# Domain.com.au Rental Listings - Data Attributes Documentation

This document provides a comprehensive overview of all data attributes extracted from Domain.com.au rental listings in the `domain_rental_listings_detailed.json` file.

## Overview

The dataset contains **50+ attributes** per listing, organized into several categories:
- Basic property information (from search results)
- Detailed property features (from individual listing pages)
- Location and address data
- Agent and agency information
- Market insights and demographics
- Property history and metadata

---

## 📋 **Attribute Categories**

### 1. **Basic Property Information** (from search results)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `listing_title` | String | Price/title displayed on search results | "From $42 pw" |
| `address_line_1` | String | First line of address | "5 Enterprise Way" |
| `suburb` | String | Suburb from search results | "YARRAWONGA" |
| `state` | String | State abbreviation | "VIC" |
| `postcode` | String | Postcode from search results | "3730" |
| `property_features` | String | Comma-delimited basic features | "1, , 1, , −," |
| `property_type` | String | Property type from search results | "Apartment / Unit / Flat" |
| `page_number` | Integer | Which search page the listing was found on | 2 |
| `url` | String | URL of the search results page | "https://www.domain.com.au/rent/?sort=price-asc&state=vic&page=2" |

### 2. **Core Property Features** (from detailed listing pages)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `beds` | Integer | Number of bedrooms | 1 |
| `baths` | Integer | Number of bathrooms | 1 |
| `parking` | Integer | Number of parking spaces | 1 |
| `property_type_detailed` | String | Detailed property type | "Apartment / Unit / Flat" |

### 3. **Address Details**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `full_address` | String | Complete formatted address | "5 Enterprise Way, Yarrawonga VIC 3730" |
| `unit_number` | String | Unit/apartment number | "2" |
| `street_number` | String | Street number | "5" |
| `street` | String | Street name | "Enterprise Way" |
| `suburb_detailed` | String | Detailed suburb name | "Yarrawonga" |
| `postcode_detailed` | String | Detailed postcode | "3730" |
| `state_abbreviation` | String | State abbreviation (lowercase) | "vic" |

### 4. **Property Identification**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `property_id` | Integer | Unique property identifier | 17240713 |
| `listing_id` | Integer | Listing ID (usually same as property_id) | 17240713 |
| `listing_url` | String | Full URL to the property listing | "https://www.domain.com.au/5-enterprise-way-yarrawonga-vic-3730-17240713" |

### 5. **Agent and Agency Information**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `agent_name` | String | Real estate agent name | "Megan Forelli" |
| `agent_phone` | String | Agent phone number | "03 5743 9500" |
| `agent_email` | String | Agent email (base64 encoded) | "bWVnYW4uZm9yZWxsaUBlbGRlcnMuY29tLmF1" |
| `agency_name` | String | Real estate agency name | "Elders Real Estate Yarrawonga" |
| `agency_logo` | String | URL to agency logo | "https://rimh2.domainstatic.com.au/..." |
| `agency_profile_url` | String | URL to agency profile page | "https://www.domain.com.au/real-estate-agencies/..." |

### 6. **Property Details**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `description` | String | Full property description | "Storage shed situation in a secure facility..." |
| `features_list` | Array | List of property features | ["Roller Door Access", "Security System"] |
| `structured_features` | Array | Structured feature data with categories | [{"name": "Roller Door Access", "category": "Other", "source": "advertiser"}] |

### 7. **Price and Status Information**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `rental_price` | String | Rental price as displayed | "From $42 pw" |
| `listing_status` | String | Current listing status | "live", "depositTaken", "recentlyUpdated" |
| `listing_tag` | String | Additional status tag | "Deposit taken" |

### 8. **Location Data**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `latitude` | Float | Property latitude coordinate | -36.0117489 |
| `longitude` | Float | Property longitude coordinate | 146.0284363 |

### 9. **Market Insights (Suburb Level)**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `median_rent_price` | Integer | Median rent price in suburb | 330 |
| `median_sold_price` | Integer | Median sold price in suburb | 255000 |
| `avg_days_on_market` | Integer | Average days on market in suburb | 59 |
| `renter_percentage` | Float | Percentage of renters in suburb | 0.4242454328832407 |
| `single_percentage` | Float | Percentage of single households in suburb | 0.5199547016557325 |

### 10. **Neighbourhood Demographics**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `age_0_to_19` | Float | Percentage of population aged 0-19 | 0.169291347 |
| `age_20_to_39` | Float | Percentage of population aged 20-39 | 0.3405512 |
| `age_40_to_59` | Float | Percentage of population aged 40-59 | 0.155511811 |
| `age_60_plus` | Float | Percentage of population aged 60+ | 0.334645659 |
| `long_term_resident` | Float | Percentage of long-term residents | 0.523809552 |
| `owner_percentage` | Float | Percentage of owner-occupiers | 0.335483879 |
| `renter_percentage_detailed` | Float | Detailed renter percentage | 0.664516151 |
| `family_percentage` | Float | Percentage of family households | 0.421052635 |
| `single_percentage_detailed` | Float | Detailed single household percentage | 0.578947365 |

### 11. **Domain Insights (Property History)**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `first_listed_date` | String | Date property was first listed | "2024-10-07T16:32:10.257" |
| `last_sold_date` | String | Date property was last sold | "2016-12-03T00:00:00" or null |
| `updated_date` | String | Date listing was last updated | "2024-10-07T16:32:10.26" |
| `number_sold` | Integer | Number of properties sold in area | 26 |

### 12. **Media and Inspection**

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `number_of_photos` | Integer | Number of photos in gallery | 5 |
| `inspection_text` | String | Inspection text/instructions | "" |
| `appointment_only` | Boolean | Whether inspection is appointment only | true |

---

## 🔍 **Data Quality Notes**

### **Missing Values**
- Some fields may be empty strings (`""`) or `null` when data is not available
- Common missing fields: `baths`, `parking`, `agent_phone`, `agent_email`
- `last_sold_date` is often `null` for rental properties

### **Data Types**
- **Integers**: `beds`, `baths`, `parking`, `property_id`, `listing_id`, `number_of_photos`
- **Floats**: All percentage and coordinate values
- **Strings**: Most text fields, dates, URLs
- **Booleans**: `appointment_only`
- **Arrays**: `features_list`, `structured_features`

### **Encoded Data**
- `agent_email` is base64 encoded and needs decoding for use
- Email format: `base64_encoded_string`

### **Date Formats**
- All dates are in ISO 8601 format: `"YYYY-MM-DDTHH:MM:SS.sss"`
- Timezone information may be included

---

## 📊 **Feature Categories for Machine Learning**

### **High-Impact Features** (Strongly correlated with price)
- `beds`, `baths`, `parking` - Core property features
- `property_type_detailed` - Property type classification
- `latitude`, `longitude` - Location coordinates
- `median_rent_price` - Market context

### **Medium-Impact Features** (Moderately correlated with price)
- `features_list` - Property amenities
- `number_of_photos` - Listing quality indicator
- `description` - Text features for NLP analysis
- `listing_status` - Market availability

### **Context Features** (Location and market dependent)
- `suburb_detailed`, `postcode_detailed` - Location identifiers
- `renter_percentage`, `single_percentage` - Demographics
- `avg_days_on_market` - Market activity
- `age_*` fields - Neighbourhood demographics

### **Derived Features** (Can be engineered)
- Price per bedroom: `rental_price / beds`
- Distance to CBD: Calculate from coordinates
- Feature count: Length of `features_list`
- Days since listed: Calculate from `first_listed_date`

---

## 🚀 **Usage Recommendations**

### **Data Cleaning**
1. Convert empty strings to `null` for missing values
2. Decode base64 encoded emails
3. Parse dates for temporal analysis
4. Extract numeric values from price strings

### **Feature Engineering**
1. Create price per bedroom/bathroom ratios
2. Calculate distance to city center
3. Extract keywords from descriptions
4. Create suburb-level aggregations

### **Model Development**
1. Use `beds`, `baths`, `parking` as primary features
2. Include location features (`latitude`, `longitude`, `suburb_detailed`)
3. Add market context (`median_rent_price`, `renter_percentage`)
4. Consider text features from `description` and `features_list`

---

## 📈 **Sample Data Statistics**

Based on the current dataset:
- **Total Listings**: 50 properties
- **Price Range**: $42/week to $380/week
- **Property Types**: Apartments, Houses, Studios, Car spaces
- **Geographic Coverage**: Various Victorian suburbs
- **Data Completeness**: Varies by field (80-95% for core features)

---

*This documentation is automatically generated from the Domain.com.au rental listings dataset. For questions or updates, refer to the data extraction pipeline.*
