# Domain.com.au Listing Page Analysis
## Property Details Found

**Title:** 2/8 Dougherty Street, Horsham VIC 3400 - Apartment For Rent | Domain
**Description:** View this 2 bedroom, 1 bathroom rental apartment at 2/8 Dougherty Street, Horsham VIC 3400. Available from Monday, 01 September 2025. Contact agent for price.

**Bedrooms:** 2
**Bathrooms:** 1

## Data Structure Analysis

### Understanding the HTML Structure

The Domain.com.au property pages use a **Next.js** framework with **Server-Side Rendering (SSR)**. The page data is embedded in the HTML as a JSON object within a `<script>` tag with the ID `__NEXT_DATA__`. This JSON contains two main sections:

#### **layoutProps** - Page-Level Configuration
`layoutProps` contains metadata and configuration for the entire page layout, including:
- **SEO metadata**: Page title, description, canonical URL
- **Feature flags**: 89+ boolean flags controlling UI features and experiments
- **User tracking**: Analytics tokens, session data, user preferences
- **Navigation data**: Breadcrumbs, header links, footer information
- **Technical settings**: Device dimensions, API endpoints, security keys

**HTML Location**: This data is embedded in the `<head>` section and used by Next.js to render the page shell.

#### **componentProps** - Property-Specific Data
`componentProps` contains all the actual property listing data that gets rendered into the page content, including:
- **Property details**: Address, bedrooms, bathrooms, features
- **Market data**: Prices, suburb insights, demographics
- **Agent information**: Contact details, agency profiles
- **Media**: Photo galleries, inspection details
- **Location data**: GPS coordinates, map information

**HTML Location**: This data is used to populate the main content area of the page, including property cards, agent sections, and market insights.

### How It Appears in HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <!-- SEO and metadata from layoutProps -->
    <title>2/8 Dougherty Street, Horsham VIC 3400 - Apartment For Rent | Domain</title>
    <meta name="description" content="View this 2 bedroom, 1 bathroom rental apartment...">
    
    <!-- Feature flags and configuration from layoutProps -->
    <script>
        window.__NEXT_DATA__ = {
            "props": {
                "pageProps": {
                    "layoutProps": {
                        "title": "2/8 Dougherty Street, Horsham VIC 3400 - Apartment For Rent | Domain",
                        "description": "View this 2 bedroom, 1 bathroom rental apartment...",
                        "featureFlags": {
                            "enableVerticalGallery": true,
                            "enableSuggestedFeatures": true,
                            // ... 89+ more feature flags
                        }
                    },
                    "componentProps": {
                        "beds": 2,
                        "baths": 1,
                        "parking": 1,
                        "address": "2/8 Dougherty Street, Horsham VIC 3400",
                        "latitude": -36.7129319,
                        "longitude": 142.1857036,
                        "median_rent_price": 328,
                        "suburbInsights": {
                            "medianPrice": 292000,
                            "avgDaysOnMarket": 77
                        },
                        // ... 100+ more property attributes
                    }
                }
            }
        };
    </script>
</head>
<body>
    <!-- The page content is rendered using componentProps data -->
    <div class="property-details">
        <!-- Property title from componentProps.listingSummary.title -->
        <h1>$380 per week</h1>
        
        <!-- Address from componentProps.address -->
        <div class="address">2/8 Dougherty Street, Horsham VIC 3400</div>
        
        <!-- Features from componentProps.beds, componentProps.baths, etc. -->
        <div class="features">2 bed, 1 bath, 1 parking</div>
        
        <!-- Market data from componentProps.suburbInsights -->
        <div class="market-info">Median rent: $328/week</div>
    </div>
</body>
</html>
```

### Data Flow in the Application

1. **Server-Side**: Next.js fetches property data from Domain's API
2. **Data Embedding**: Both `layoutProps` and `componentProps` are serialized into the `__NEXT_DATA__` script tag
3. **Client-Side Hydration**: JavaScript reads this data to render the interactive components
4. **Dynamic Updates**: Some data may be updated via additional API calls

### Why This Structure Matters for Scraping

- **Complete Data Access**: All property information is available in one JSON object
- **Structured Format**: Data is already parsed and organized, not scattered across HTML elements
- **Consistent Schema**: Same structure across all property pages
- **Rich Metadata**: Includes market insights, demographics, and historical data not visible in the rendered HTML

- **layoutProps**: dict with 14 items
- **layoutProps.title**: str = 2/8 Dougherty Street, Horsham VIC 3400 - Apartment For Rent | Domain
- **layoutProps.description**: str (long text: View this 2 bedroom, 1 bathroom rental apartment at 2/8 Dougherty Street, Horsham VIC 3400. Availabl...)
- **layoutProps.canonical**: str = https://www.domain.com.au/2-8-dougherty-street-horsham-vic-3400-17712152
- **layoutProps.metatags**: list with 24 items
- **layoutProps.metatags**: List with 24 items
- **layoutProps.isArchived**: bool = False
- **layoutProps.disableAds**: bool = False
- **layoutProps.disableTracking**: bool = False
- **layoutProps.isFromEu**: bool = False
- **layoutProps.digitalData**: dict with 8 items
- **layoutProps.digitalData.page**: dict with 3 items
- **layoutProps.digitalData.titan**: dict with 5 items
- **layoutProps.digitalData.titanFromGraph**: dict with 5 items
- **layoutProps.digitalData.adLoader**: str = prebid
- **layoutProps.digitalData.pageFromGraph**: dict with 3 items
- **layoutProps.digitalData.version**: str = 1.0
- **layoutProps.digitalData.events**: list = []
- **layoutProps.digitalData.user**: dict with 5 items
- **layoutProps.jsonLdItems**: list with 4 items
- **layoutProps.jsonLdItems**: List with 4 items
- **layoutProps.raygunTags**: list with 2 items
- **layoutProps.raygunTags**: List with 2 items
- **layoutProps.featureFlags**: dict with 89 items
- **layoutProps.featureFlags.enableContentSnippet**: bool = False
- **layoutProps.featureFlags.enableContentSnippetWithPostcodes**: bool = False
- **layoutProps.featureFlags.disableAdsFlag**: bool = False
- **layoutProps.featureFlags.enableEnquiryCustomisations**: bool = False
- **layoutProps.featureFlags.shortlistExperimentFlag**: bool = True
- **layoutProps.featureFlags.enableSuggestedFeatures**: bool = True
- **layoutProps.featureFlags.enableAdditionalDescriptionFeature**: bool = True
- **layoutProps.featureFlags.enableVerticalGallery**: bool = True
- **layoutProps.featureFlags.enableRetirements**: bool = True
- **layoutProps.featureFlags.enablePropertyNextSteps**: bool = True
- **layoutProps.featureFlags.enablePropertyNextStepsBackend**: bool = True
- **layoutProps.featureFlags.enableAddNotes**: bool = False
- **layoutProps.featureFlags.textAdsEnabled**: bool = True
- **layoutProps.featureFlags.enableMobileBannerAppDriver**: bool = False
- **layoutProps.featureFlags.enableCustomSort**: bool = True
- **layoutProps.featureFlags.enableMRECAd**: bool = False
- **layoutProps.featureFlags.enableVectorGoogleMaps**: bool = False
- **layoutProps.featureFlags.enableBranch**: bool = True
- **layoutProps.featureFlags.googleOneTap**: bool = True
- **layoutProps.featureFlags.schoolSearchMapView**: bool = True
- **layoutProps.featureFlags.enablePropertyAlertPaginationCTA**: bool = False
- **layoutProps.featureFlags.enableIndependentOne**: bool = False
- **layoutProps.featureFlags.enableIndependentTwo**: bool = False
- **layoutProps.featureFlags.enableIndependentThree**: bool = True
- **layoutProps.featureFlags.enableHomePagePropertyAlert**: bool = True
- **layoutProps.featureFlags.enableShortlistPhotoGallery**: bool = False
- **layoutProps.featureFlags.enablePropertyAlertOverlay**: bool = True
- **layoutProps.featureFlags.enableShortlistNotesEditing**: bool = False
- **layoutProps.featureFlags.enableShortlistNotesEditingMobile**: bool = False
- **layoutProps.featureFlags.enableShortlistSignupDriverMl**: bool = True
- **layoutProps.featureFlags.enableShortlistSignupDriverSimple**: bool = False
- **layoutProps.featureFlags.enableHomepageSchoolFirstTypeahead**: bool = True
- **layoutProps.featureFlags.enableGraphQLSuggestLocations**: bool = True
- **layoutProps.featureFlags.shareShortlistBranchExperiment**: bool = False
- **layoutProps.featureFlags.enableNewDevelopmentEnquiryForm**: bool = False
- **layoutProps.featureFlags.enableTypeaheadSchoolMessage**: bool = False
- **layoutProps.featureFlags.enableSuggestSuburbNewPill**: bool = False
- **layoutProps.featureFlags.enableBuyerTypeExperiment**: bool = False
- **layoutProps.featureFlags.enableBuyerTypeExperimentStarted**: bool = False
- **layoutProps.featureFlags.mobileWebThirdPartyRentalButton**: bool = True
- **layoutProps.featureFlags.enableUPVExperiment**: bool = True
- **layoutProps.featureFlags.enableNewProjectListingViewMore**: bool = True
- **layoutProps.featureFlags.enableRequestFloorPlanForChildListing**: bool = False
- **layoutProps.featureFlags.enableSearchDisplayPriceRange**: bool = False
- **layoutProps.featureFlags.enableGraphQLSearch**: bool = False
- **layoutProps.featureFlags.enableGraphQLSavedSearch**: bool = False
- **layoutProps.featureFlags.topspotGQL**: bool = False
- **layoutProps.featureFlags.enableBYBTextlink**: bool = False
- **layoutProps.featureFlags.enableGQLOnListingsPage**: bool = True
- **layoutProps.featureFlags.enableListingsPageGQLMapping**: bool = False
- **layoutProps.featureFlags.immediateEmailNotifications**: bool = False
- **layoutProps.featureFlags.postInspectionAd**: bool = False
- **layoutProps.featureFlags.postEnquiryAd**: bool = True
- **layoutProps.featureFlags.enableGraphQLUPVSoldListings**: bool = False
- **layoutProps.featureFlags.premarketListingGQL**: bool = False
- **layoutProps.featureFlags.enableGraphQLFeaturedAgency**: bool = True
- **layoutProps.featureFlags.enableGraphQLTopspot**: bool = True
- **layoutProps.featureFlags.platinumListingGalleryAds**: bool = True
- **layoutProps.featureFlags.disableProjectVerticalGallery**: bool = True
- **layoutProps.featureFlags.priceGuideExp**: bool = True
- **layoutProps.featureFlags.enableGraphQLNewToYou**: bool = True
- **layoutProps.featureFlags.platinumListingsInlineEnquiryExp**: bool = False
- **layoutProps.featureFlags.twoColumnExperimentForPlatinumListings**: bool = False
- **layoutProps.featureFlags.enableRequestFloorPlanExp**: bool = False
- **layoutProps.featureFlags.enablePpid**: bool = True
- **layoutProps.featureFlags.enableRentalFormDataFromGQL**: bool = True
- **layoutProps.featureFlags.enableRentalListingPageUpdates**: bool = True
- **layoutProps.featureFlags.disableSwipeToCloseFBBrowser**: bool = True
- **layoutProps.featureFlags.enableSchoolSlugMapRemoval**: bool = True
- **layoutProps.featureFlags.enableListingMediaAds**: bool = True
- **layoutProps.featureFlags.enableListingMediaAdUnloan**: bool = False
- **layoutProps.featureFlags.enableListingMediaAdLiberty**: bool = True
- **layoutProps.featureFlags.enableListingMediaAdAussieBroadband**: bool = False
- **layoutProps.featureFlags.enableListingMediaAdAllianz**: bool = True
- **layoutProps.featureFlags.enableListingMediaAdNBN**: bool = True
- **layoutProps.featureFlags.galleryControlsExperiment**: bool = False
- **layoutProps.featureFlags.enablePropertyAlertModal**: bool = False
- **layoutProps.featureFlags.enableMiniGalleryPreviewExp**: bool = True
- **layoutProps.featureFlags.verticalGalleryExperiment**: bool = False
- **layoutProps.featureFlags.enableGoogleOneTapSearchPage**: bool = True
- **layoutProps.featureFlags.enableGoogleOneTapListingPage**: bool = False
- **layoutProps.featureFlags.stickyAgentCardRentalListing**: bool = True
- **layoutProps.featureFlags.enableEnquiryRecaptcha**: bool = True
- **layoutProps.featureFlags.enableEnquiryRecaptchaLoginBypass**: bool = True
- **layoutProps.featureFlags.enableEnquiryRecaptchaV2Fallback**: bool = True
- **layoutProps.featureFlags.enableVendorLeadCTA**: bool = False
- **layoutProps.featureFlags.enableVendorLeadCTABranded**: bool = False
- **layoutProps.featureFlags.enableVendorLeadCTAOnTop**: bool = False
- **layoutProps.featureFlags.startBuyerTypeExperiment**: bool = False
- **layoutProps.heroImages**: list with 3 items
- **layoutProps.heroImages**: List with 3 items
- **layoutProps.ppid**: str = 28f4d37863d92f911311611d313c0e438a1083b59e443ad2a069276e0477ddcb
- **componentProps**: dict with 108 items
- **componentProps.user**: NoneType = None
- **componentProps.loginAndReturnUrl**: str (long text: https://www.domain.com.au/authentications/login?ReturnUrl=%2F2-8-dougherty-street-horsham-vic-3400-1...)
- **componentProps.signupAndReturnUrl**: str (long text: https://www.domain.com.au/authentications/signup?ReturnUrl=%2F2-8-dougherty-street-horsham-vic-3400-...)
- **componentProps.notificationApiUrl**: str = https://www.domain.com.au/sls-widgets-api
- **componentProps.listingsMap**: dict with 21 items
- **componentProps.listingsMap.16192449**: dict with 5 items
- **componentProps.listingsMap.16566039**: dict with 5 items
- **componentProps.listingsMap.16878242**: dict with 5 items
- **componentProps.listingsMap.17559978**: dict with 5 items
- **componentProps.listingsMap.17626205**: dict with 5 items
- **componentProps.listingsMap.17645154**: dict with 5 items
- **componentProps.listingsMap.17686324**: dict with 5 items
- **componentProps.listingsMap.17687609**: dict with 5 items
- **componentProps.listingsMap.17690514**: dict with 5 items
- **componentProps.listingsMap.17695059**: dict with 5 items
- **componentProps.listingsMap.17707882**: dict with 5 items
- **componentProps.listingsMap.17709348**: dict with 5 items
- **componentProps.listingsMap.17709975**: dict with 5 items
- **componentProps.listingsMap.17712152**: dict with 3 items
- **componentProps.listingsMap.17712519**: dict with 5 items
- **componentProps.listingsMap.17721130**: dict with 5 items
- **componentProps.listingsMap.17731910**: dict with 5 items
- **componentProps.listingsMap.17732511**: dict with 5 items
- **componentProps.listingsMap.17733680**: dict with 5 items
- **componentProps.listingsMap.17737379**: dict with 5 items
- **componentProps.listingsMap.17737382**: dict with 5 items
- **componentProps.otherListingsIds**: list with 20 items
- **componentProps.otherListingsIds**: List with 20 items
- **componentProps.address**: str = 2/8 Dougherty Street, Horsham VIC 3400
- **componentProps.unitNumber**: str = 2
- **componentProps.streetNumber**: str = 8
- **componentProps.street**: str = Dougherty Street
- **componentProps.suburb**: str = Horsham
- **componentProps.postcode**: str = 3400
- **componentProps.stateAbbreviation**: str = vic
- **componentProps.projectColor**: str = 
- **componentProps.createdOn**: str = 2025-08-12T15:51:07.087
- **componentProps.modifiedOn**: str = 2025-08-12T15:51:07.09
- **componentProps.projectName**: NoneType = None
- **componentProps.isStandardListing**: bool = False
- **componentProps.isArchived**: bool = False
- **componentProps.id**: int = 17712152
- **componentProps.listingId**: int = 17712152
- **componentProps.listingUrl**: str = https://www.domain.com.au/2-8-dougherty-street-horsham-vic-3400-17712152
- **componentProps.projectUrl**: NoneType = None
- **componentProps.bigProjectLogo**: NoneType = None
- **componentProps.smallProjectLogo**: NoneType = None
- **componentProps.brandingProjectLogo**: NoneType = None
- **componentProps.brandingProjectColor**: NoneType = None
- **componentProps.footer**: dict with 5 items
- **componentProps.footer.baseUrl**: str = https://www.domain.com.au
- **componentProps.footer.suburb**: dict with 2 items
- **componentProps.footer.sale**: dict with 4 items
- **componentProps.footer.rent**: dict with 3 items
- **componentProps.footer.surroundingSuburbs**: list with 4 items
- **componentProps.propertyType**: str = Apartment / Unit / Flat
- **componentProps.beds**: int = 2
- **componentProps.phone**: str = 0409554955
- **componentProps.agencyName**: str = Wimmera Property Agents
- **componentProps.propertyDeveloperName**: str = Wimmera Property Agents
- **componentProps.agencyLogo**: str (long text: https://rimh2.domainstatic.com.au/brwzhVjxilfsbsW47cUNy7QRi2o=/filters:format(png):quality(80):no_up...)
- **componentProps.agencyProfileUrl**: str = https://www.domain.com.au/real-estate-agencies/wimmerapropertyagents-38727/
- **componentProps.propertyDeveloperUrl**: str = https://www.domain.com.au/real-estate-agencies/wimmerapropertyagents-38727/
- **componentProps.projectLink**: str = http://www.wimmerapropertyagents.com.au
- **componentProps.websiteLink**: str = 
- **componentProps.brandingColor**: str = #99CBC0
- **componentProps.brandingAppearance**: str = light
- **componentProps.limitedAgencyMode**: bool = False
- **componentProps.listingType**: str = residential
- **componentProps.description**: list with 2 items
- **componentProps.description**: List with 2 items
- **componentProps.fetchUrl**: str = https://www.domain.com.au
- **componentProps.headline**: str = UNDER APPLICATION
- **componentProps.tagline**: str = 
- **componentProps.banner**: NoneType = None
- **componentProps.schoolCatchment**: dict with 7 items
- **componentProps.schoolCatchment.schools**: list with 6 items
- **componentProps.schoolCatchment.numberOfVisibleSchools**: int = 3
- **componentProps.schoolCatchment.enableSchoolProfileLink**: bool = True
- **componentProps.schoolCatchment.ads**: dict with 2 items
- **componentProps.schoolCatchment.addressParts**: dict with 8 items
- **componentProps.schoolCatchment.adId**: str = 17712152
- **componentProps.schoolCatchment.feedbackUrl**: str = /phoenix/api/school-data/report-error
- **componentProps.whatIsNearby**: dict = {}
- **componentProps.neighbourhoodInsights**: dict with 11 items
- **componentProps.neighbourhoodInsights.age0To19**: float = 0.265734255
- **componentProps.neighbourhoodInsights.age20To39**: float = 0.230769217
- **componentProps.neighbourhoodInsights.age40To59**: float = 0.230769232
- **componentProps.neighbourhoodInsights.age60Plus**: float = 0.272727281
- **componentProps.neighbourhoodInsights.longTermResident**: float = 0.565947235
- **componentProps.neighbourhoodInsights.owner**: float = 0.6521739
- **componentProps.neighbourhoodInsights.renter**: float = 0.3478261
- **componentProps.neighbourhoodInsights.family**: float = 0.58
- **componentProps.neighbourhoodInsights.single**: float = 0.42
- **componentProps.neighbourhoodInsights.map**: dict with 1 items
- **componentProps.neighbourhoodInsights.showIncomeAndExpenses**: bool = False
- **componentProps.locationProfileCards**: dict with 1 items
- **componentProps.locationProfileCards.profiles**: list with 2 items
- **componentProps.suburbInsights**: dict with 16 items
- **componentProps.suburbInsights.beds**: int = 2
- **componentProps.suburbInsights.propertyType**: str = Unit
- **componentProps.suburbInsights.suburb**: str = Horsham
- **componentProps.suburbInsights.suburbProfileUrl**: str = /suburb-profile/horsham-vic-3400
- **componentProps.suburbInsights.medianPrice**: int = 292000
- **componentProps.suburbInsights.medianRentPrice**: int = 328
- **componentProps.suburbInsights.avgDaysOnMarket**: int = 77
- **componentProps.suburbInsights.auctionClearance**: int = 0
- **componentProps.suburbInsights.nrSoldThisYear**: int = 13
- **componentProps.suburbInsights.entryLevelPrice**: int = 240000
- **componentProps.suburbInsights.luxuryLevelPrice**: int = 395000
- **componentProps.suburbInsights.renterPercentage**: float = 0.3103750438135296
- **componentProps.suburbInsights.singlePercentage**: float = 0.5300624894443506
- **componentProps.suburbInsights.demographics**: dict with 7 items
- **componentProps.suburbInsights.salesGrowthList**: list with 6 items
- **componentProps.suburbInsights.mostRecentSale**: NoneType = None
- **componentProps.otherProjects**: list = []
- **componentProps.gallery**: dict with 1 items
- **componentProps.gallery.slides**: list with 8 items
- **componentProps.additionalLinks**: dict with 1 items
- **componentProps.additionalLinks.brochureLink**: NoneType = None
- **componentProps.header**: dict with 5 items
- **componentProps.header.breadcrumbs**: list with 6 items
- **componentProps.header.baseUrl**: str = www.domain.com.au
- **componentProps.header.signupUrl**: str = https://www.domain.com.au//authentications/signup
- **componentProps.header.logoutUrl**: str = https://www.domain.com.au//authentications/logoff
- **componentProps.header.loginUrl**: str = https://www.domain.com.au//authentications/login
- **componentProps.listingSummary**: dict with 16 items
- **componentProps.listingSummary.address**: str = 2/8 Dougherty Street, Horsham VIC 3400
- **componentProps.listingSummary.baths**: int = 1
- **componentProps.listingSummary.beds**: int = 2
- **componentProps.listingSummary.houses**: int = 0
- **componentProps.listingSummary.isRural**: bool = False
- **componentProps.listingSummary.listingType**: str = rent
- **componentProps.listingSummary.mode**: str = rent
- **componentProps.listingSummary.parking**: int = 1
- **componentProps.listingSummary.promoType**: str = branded
- **componentProps.listingSummary.propertyType**: str = Apartment / Unit / Flat
- **componentProps.listingSummary.showDefaultFeatures**: bool = True
- **componentProps.listingSummary.showDomainInsight**: bool = False
- **componentProps.listingSummary.stats**: list with 2 items
- **componentProps.listingSummary.status**: str = depositTaken
- **componentProps.listingSummary.tag**: str = Deposit taken
- **componentProps.listingSummary.title**: str = $380 per week
- **componentProps.agents**: list with 1 items
- **componentProps.agents**: List with 1 items
- **componentProps.inspection**: dict with 9 items
- **componentProps.inspection.inspectionText**: str = 
- **componentProps.inspection.displayAddress**: str = 2/8 Dougherty Street, Horsham VIC 3400
- **componentProps.inspection.displayStreetNumber**: str = 8
- **componentProps.inspection.displayStreet**: str = Dougherty Street
- **componentProps.inspection.displaySuburb**: str = Horsham
- **componentProps.inspection.displayState**: str = VIC
- **componentProps.inspection.displayPostcode**: str = 3400
- **componentProps.inspection.appointmentOnly**: bool = True
- **componentProps.inspection.timeZone**: str = Australia/Melbourne
- **componentProps.features**: list with 3 items
- **componentProps.features**: List with 3 items
- **componentProps.structuredFeatures**: list with 5 items
- **componentProps.structuredFeatures**: List with 5 items
- **componentProps.priceGuide**: dict with 8 items
- **componentProps.priceGuide.agencyName**: str = Wimmera Property Agents
- **componentProps.priceGuide.agents**: list with 1 items
- **componentProps.priceGuide.theme**: str = domain
- **componentProps.priceGuide.estimatedPrice**: dict with 2 items
- **componentProps.priceGuide.suburbMedianPrice**: dict with 7 items
- **componentProps.priceGuide.comparableData**: dict with 1 items
- **componentProps.priceGuide.pdfLink**: NoneType = None
- **componentProps.priceGuide.state**: str = VIC
- **componentProps.stampDutyEstimate**: NoneType = None
- **componentProps.map**: dict with 10 items
- **componentProps.map.apiKey**: str = AIzaSyCx5gZA9rTOwBUcbFuiEk12Y87Pn7VKCak
- **componentProps.map.latitude**: float = -36.7129319
- **componentProps.map.longitude**: float = 142.1857036
- **componentProps.map.displayCentreLatitude**: NoneType = None
- **componentProps.map.displayCentreLongitude**: NoneType = None
- **componentProps.map.displayCentreAddress**: str = 
- **componentProps.map.suburbProfileUrl**: str = https://www.domain.com.au/suburb-profile/horsham-vic-3400
- **componentProps.map.hasDisplayCentre**: bool = False
- **componentProps.map.placesLoggedIn**: bool = False
- **componentProps.map.placesScrollPosition**: int = -1
- **componentProps.domainSays**: dict with 12 items
- **componentProps.domainSays.firstListedDate**: str = 2025-08-12T15:51:07.087
- **componentProps.domainSays.forSalePropertiesUrl**: str = /sale/horsham-vic-3400/apartment-unit-flat/2-bedrooms/?ssubs=0
- **componentProps.domainSays.lastSoldOnDate**: NoneType = None
- **componentProps.domainSays.listingMode**: str = rent
- **componentProps.domainSays.medianRentPrice**: int = 328
- **componentProps.domainSays.medianSoldPrice**: int = 292000
- **componentProps.domainSays.numberSold**: int = 13
- **componentProps.domainSays.propertyCategoryForSale**: int = 5
- **componentProps.domainSays.soldPropertiesUrl**: str = /sold-listings/horsham-vic-3400/apartment-unit-flat/2-bedrooms/?ssubs=0
- **componentProps.domainSays.updatedDate**: str = 2025-08-12T15:51:07.09
- **componentProps.domainSays.storyPropertyType**: str = Unit
- **componentProps.domainSays.propertyBedrooms**: int = 2
- **componentProps.meta**: dict with 2 items
- **componentProps.meta.baseUrl**: str = https://www.domain.com.au/
- **componentProps.meta.loginUrl**: str = https://www.domain.com.au//authentications/login
- **componentProps.enquiryForm**: dict with 2 items
- **componentProps.enquiryForm.enquiryUrl**: str = /phoenix/api/simple-enquiry
- **componentProps.enquiryForm.buyerTypes**: list with 4 items
- **componentProps.thumborBaseUrl**: str = 
- **componentProps.oneFormOptIn**: bool = False
- **componentProps.thirdPartyApplyData**: NoneType = None
- **componentProps.thirdPartyBookingData**: NoneType = None
- **componentProps.estimatedDeviceWidth**: str = 1440px
- **componentProps.estimatedDeviceHeight**: str = 1024px
- **componentProps.noAds**: bool = False
- **componentProps.fetchAndPublishUserData**: bool = True
- **componentProps.shortlistExperimentFlag**: bool = True
- **componentProps.isLandEstate**: bool = False
- **componentProps.requiresTrackingConsent**: bool = False
- **componentProps.placesEnabled**: bool = True
- **componentProps.displayType**: str = fullAddress
- **componentProps.backToSearchUrl**: str = https://www.domain.com.au/rent/?sort=price-asc&state=vic&page=46
- **componentProps.canGoBackToSearch**: bool = True
- **componentProps.primaryPropertyType**: str = Any
- **componentProps.propertyId**: NoneType = None
- **componentProps.rentalApplicationActive**: bool = False
- **componentProps.rentalApplicationData**: dict with 4 items
- **componentProps.rentalApplicationData.id**: NoneType = None
- **componentProps.rentalApplicationData.status**: str = 
- **componentProps.rentalApplicationData.progress**: int = 0
- **componentProps.rentalApplicationData.url**: str = 
- **componentProps.enableDownloadPropertyReport**: bool = False
- **componentProps.enableMobileBannerAppDriver**: bool = False
- **componentProps.forceMobileBannerAppDriver**: bool = False
- **componentProps.enableSuggestedFeatures**: bool = True
- **componentProps.enableVerticalGallery**: bool = True
- **componentProps.enableHomepassAPIV2**: bool = False
- **componentProps.featureFlags**: dict with 89 items
- **componentProps.featureFlags.enableContentSnippet**: bool = False
- **componentProps.featureFlags.enableContentSnippetWithPostcodes**: bool = False
- **componentProps.featureFlags.disableAdsFlag**: bool = False
- **componentProps.featureFlags.enableEnquiryCustomisations**: bool = False
- **componentProps.featureFlags.shortlistExperimentFlag**: bool = True
- **componentProps.featureFlags.enableSuggestedFeatures**: bool = True
- **componentProps.featureFlags.enableAdditionalDescriptionFeature**: bool = True
- **componentProps.featureFlags.enableVerticalGallery**: bool = True
- **componentProps.featureFlags.enableRetirements**: bool = True
- **componentProps.featureFlags.enablePropertyNextSteps**: bool = True
- **componentProps.featureFlags.enablePropertyNextStepsBackend**: bool = True
- **componentProps.featureFlags.enableAddNotes**: bool = False
- **componentProps.featureFlags.textAdsEnabled**: bool = True
- **componentProps.featureFlags.enableMobileBannerAppDriver**: bool = False
- **componentProps.featureFlags.enableCustomSort**: bool = True
- **componentProps.featureFlags.enableMRECAd**: bool = False
- **componentProps.featureFlags.enableVectorGoogleMaps**: bool = False
- **componentProps.featureFlags.enableBranch**: bool = True
- **componentProps.featureFlags.googleOneTap**: bool = True
- **componentProps.featureFlags.schoolSearchMapView**: bool = True
- **componentProps.featureFlags.enablePropertyAlertPaginationCTA**: bool = False
- **componentProps.featureFlags.enableIndependentOne**: bool = False
- **componentProps.featureFlags.enableIndependentTwo**: bool = False
- **componentProps.featureFlags.enableIndependentThree**: bool = True
- **componentProps.featureFlags.enableHomePagePropertyAlert**: bool = True
- **componentProps.featureFlags.enableShortlistPhotoGallery**: bool = False
- **componentProps.featureFlags.enablePropertyAlertOverlay**: bool = True
- **componentProps.featureFlags.enableShortlistNotesEditing**: bool = False
- **componentProps.featureFlags.enableShortlistNotesEditingMobile**: bool = False
- **componentProps.featureFlags.enableShortlistSignupDriverMl**: bool = True
- **componentProps.featureFlags.enableShortlistSignupDriverSimple**: bool = False
- **componentProps.featureFlags.enableHomepageSchoolFirstTypeahead**: bool = True
- **componentProps.featureFlags.enableGraphQLSuggestLocations**: bool = True
- **componentProps.featureFlags.shareShortlistBranchExperiment**: bool = False
- **componentProps.featureFlags.enableNewDevelopmentEnquiryForm**: bool = False
- **componentProps.featureFlags.enableTypeaheadSchoolMessage**: bool = False
- **componentProps.featureFlags.enableSuggestSuburbNewPill**: bool = False
- **componentProps.featureFlags.enableBuyerTypeExperiment**: bool = False
- **componentProps.featureFlags.enableBuyerTypeExperimentStarted**: bool = False
- **componentProps.featureFlags.mobileWebThirdPartyRentalButton**: bool = True
- **componentProps.featureFlags.enableUPVExperiment**: bool = True
- **componentProps.featureFlags.enableNewProjectListingViewMore**: bool = True
- **componentProps.featureFlags.enableRequestFloorPlanForChildListing**: bool = False
- **componentProps.featureFlags.enableSearchDisplayPriceRange**: bool = False
- **componentProps.featureFlags.enableGraphQLSearch**: bool = False
- **componentProps.featureFlags.enableGraphQLSavedSearch**: bool = False
- **componentProps.featureFlags.topspotGQL**: bool = False
- **componentProps.featureFlags.enableBYBTextlink**: bool = False
- **componentProps.featureFlags.enableGQLOnListingsPage**: bool = True
- **componentProps.featureFlags.enableListingsPageGQLMapping**: bool = False
- **componentProps.featureFlags.immediateEmailNotifications**: bool = False
- **componentProps.featureFlags.postInspectionAd**: bool = False
- **componentProps.featureFlags.postEnquiryAd**: bool = True
- **componentProps.featureFlags.enableGraphQLUPVSoldListings**: bool = False
- **componentProps.featureFlags.premarketListingGQL**: bool = False
- **componentProps.featureFlags.enableGraphQLFeaturedAgency**: bool = True
- **componentProps.featureFlags.enableGraphQLTopspot**: bool = True
- **componentProps.featureFlags.platinumListingGalleryAds**: bool = True
- **componentProps.featureFlags.disableProjectVerticalGallery**: bool = True
- **componentProps.featureFlags.priceGuideExp**: bool = True
- **componentProps.featureFlags.enableGraphQLNewToYou**: bool = True
- **componentProps.featureFlags.platinumListingsInlineEnquiryExp**: bool = False
- **componentProps.featureFlags.twoColumnExperimentForPlatinumListings**: bool = False
- **componentProps.featureFlags.enableRequestFloorPlanExp**: bool = False
- **componentProps.featureFlags.enablePpid**: bool = True
- **componentProps.featureFlags.enableRentalFormDataFromGQL**: bool = True
- **componentProps.featureFlags.enableRentalListingPageUpdates**: bool = True
- **componentProps.featureFlags.disableSwipeToCloseFBBrowser**: bool = True
- **componentProps.featureFlags.enableSchoolSlugMapRemoval**: bool = True
- **componentProps.featureFlags.enableListingMediaAds**: bool = True
- **componentProps.featureFlags.enableListingMediaAdUnloan**: bool = False
- **componentProps.featureFlags.enableListingMediaAdLiberty**: bool = True
- **componentProps.featureFlags.enableListingMediaAdAussieBroadband**: bool = False
- **componentProps.featureFlags.enableListingMediaAdAllianz**: bool = True
- **componentProps.featureFlags.enableListingMediaAdNBN**: bool = True
- **componentProps.featureFlags.galleryControlsExperiment**: bool = False
- **componentProps.featureFlags.enablePropertyAlertModal**: bool = False
- **componentProps.featureFlags.enableMiniGalleryPreviewExp**: bool = False
- **componentProps.featureFlags.verticalGalleryExperiment**: bool = False
- **componentProps.featureFlags.enableGoogleOneTapSearchPage**: bool = True
- **componentProps.featureFlags.enableGoogleOneTapListingPage**: bool = False
- **componentProps.featureFlags.stickyAgentCardRentalListing**: bool = True
- **componentProps.featureFlags.enableEnquiryRecaptcha**: bool = True
- **componentProps.featureFlags.enableEnquiryRecaptchaLoginBypass**: bool = True
- **componentProps.featureFlags.enableEnquiryRecaptchaV2Fallback**: bool = True
- **componentProps.featureFlags.enableVendorLeadCTA**: bool = False
- **componentProps.featureFlags.enableVendorLeadCTABranded**: bool = False
- **componentProps.featureFlags.enableVendorLeadCTAOnTop**: bool = False
- **componentProps.featureFlags.startBuyerTypeExperiment**: bool = False
- **componentProps.mixpanelToken**: str = ab0bde70050c3eabaaf8824402fa01e0
- **componentProps.sessionToken**: str = 84f8b7b8-a3f3-4ad1-8d2a-76b904d53a99
- **componentProps.isRetirement**: bool = False
- **componentProps.faqs**: list with 7 items
- **componentProps.faqs**: List with 7 items
- **componentProps.shortlistPriceChange**: NoneType = None
- **componentProps.correlationId**: str = 402d13ed-342c-4078-8395-900cd425deba
- **componentProps.isRedirectedFromPremarket**: bool = False
- **componentProps.graphqlApi**: str = https://www.domain.com.au/graphql
- **componentProps.enableBeforeYouBidNew**: bool = True
- **componentProps.enableEnquiryCustomisations**: bool = False
- **componentProps.recaptchaSiteKey**: str = 6LeDUaUbAAAAALoyaiI4Yv9TKESEc727OK6H0SmK
- **componentProps.recaptchaSiteKeyV2**: str = 6LeYd44rAAAAACY1tpXGEmJY8vjBr35RWnEzSSVG
- **componentProps.projectDetails**: dict with 3 items
- **componentProps.projectDetails.brochureLink**: NoneType = None
- **componentProps.projectDetails.masterPlan**: NoneType = None
- **componentProps.projectDetails.projectCategory**: NoneType = None
- **componentProps.rootGraphQuery**: dict with 1 items
- **componentProps.rootGraphQuery.listingByIdV2**: dict with 49 items
- **componentProps.userAgent**: str = Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36

## Features Relevant for Rental Price Prediction

### High-Impact Features (Strongly Correlated with Price):
- **Bedrooms** - Number of bedrooms (most important factor)
- **Bathrooms** - Number of bathrooms
- **Property Type** - House, Apartment, Unit, Townhouse, etc.
- **Location** - Suburb, postcode, distance to city center
- **Parking** - Number of car spaces/garage
- **Floor Area** - Size of the property in square meters

### Medium-Impact Features (Moderately Correlated with Price):
- **Year Built** - Age of the property
- **Condition** - New, renovated, needs work, etc.
- **Amenities** - Pool, gym, balcony, garden, etc.
- **Furnished Status** - Fully furnished, partially furnished, unfurnished
- **Building Features** - Elevator, air conditioning, heating, etc.
- **Outdoor Space** - Balcony, garden, courtyard size

### Location-Based Features (Context-Dependent):
- **Distance to CBD** - Proximity to city center
- **Public Transport** - Distance to train/bus stops
- **Schools** - Quality and proximity of nearby schools
- **Shopping** - Distance to shopping centers
- **Crime Rate** - Safety of the area
- **Demographics** - Age profile, income levels of residents

### Market Features (External Factors):
- **Rental Yield** - Historical rental returns in the area
- **Capital Growth** - Property value appreciation trends
- **Supply/Demand** - Number of available properties vs. demand
- **Seasonal Factors** - Time of year, market conditions
- **Agent/Listing Quality** - Professional presentation, photos, etc.

## Data Extraction Recommendations

Based on the analysis, the following data should be prioritized for extraction:

### 1. Core Property Features
- Bedrooms (number)
- Bathrooms (number)
- Parking spaces (number)
- Property type (house, apartment, etc.)
- Floor area (square meters)
- Year built/age

### 2. Location Data
- Full address (street, suburb, state, postcode)
- Distance to CBD (if available)
- Distance to nearest train station
- School catchment areas

### 3. Property Condition & Amenities
- Furnished status
- Air conditioning
- Heating
- Balcony/outdoor space
- Garden/yard
- Pool
- Gym/fitness facilities

### 4. Market Context
- Days on market
- Price history (if available)
- Similar properties in area
- Rental yield data

### 5. Agent/Listing Quality
- Number of photos
- Quality of description
- Agent experience/rating
- Inspection availability

## Implementation Notes

1. **Data Quality**: Ensure consistent data types (numbers for bedrooms, bathrooms, etc.)
2. **Missing Data**: Handle missing values appropriately (imputation vs. exclusion)
3. **Feature Engineering**: Create derived features like 'price_per_sqm', 'bedroom_bathroom_ratio'
4. **Location Encoding**: Use postcode or suburb as categorical features, or geocode to lat/lng
5. **Text Features**: Extract keywords from descriptions for amenities and condition
6. **Temporal Features**: Consider seasonality and market timing

## Next Steps

1. Update the spider to extract these additional features
2. Implement data validation and cleaning pipelines
3. Create feature engineering functions
4. Build a comprehensive dataset for price prediction modeling
