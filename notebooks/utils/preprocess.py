import pandas as pd
import pickle
import os


class PreprocessUtils:
    """
    A utility class for preprocessing operations on data.
    """

    def __init__(self, mapping_path="../data/processed/mapping.pkl"):
        """
        Initialize the PreprocessUtils class.

        Parameters:
        -----------
        mapping_path : str
            Path to the suburb mapping pickle file
        """
        self.mapping_path = mapping_path
        self.suburb_mapping = None
        self.inverted_suburb_mapping = None

    def _load_suburb_mapping(self):
        """
        Load the suburb mapping from pickle file if not already loaded.
        """
        if self.suburb_mapping is None:
            self.suburb_mapping = pickle.load(open(self.mapping_path, "rb"))
            self._create_inverted_mapping()

    def _create_inverted_mapping(self):
        """
        Create inverted dictionary for reverse mapping (value -> key).
        Handle case where values might be lists.
        """
        self.inverted_suburb_mapping = {}
        for key, value in self.suburb_mapping.items():
            if isinstance(value, list):
                # If value is a list, map each item in the list to the key
                for item in value:
                    self.inverted_suburb_mapping[item] = key
            else:
                # If value is a single item, map it directly
                self.inverted_suburb_mapping[value] = key

    def map_suburb(self, suburb_series):
        """
        Map suburbs to their standardized names using the suburb mapping.

        Parameters:
        -----------
        suburb_series : pd.Series
            A pandas Series containing suburb names

        Returns:
        --------
        pd.Series
            A pandas Series with mapped suburb names
        """
        # Load the mapping if not already loaded
        self._load_suburb_mapping()

        # Create a copy to avoid modifying the original
        suburb_series_copy = suburb_series.copy()

        # Ensure lowercasing
        suburb_series_copy = suburb_series_copy.str.lower()

        # Create mapped_suburb column using the inverted dictionary
        mapped_suburb = suburb_series_copy.map(self.inverted_suburb_mapping)

        # Fill NaN values (unmapped suburbs) with the original lowercased suburb
        mapped_suburb = mapped_suburb.fillna(suburb_series_copy)

        return mapped_suburb

    def map_property_type(self, property_type_series):
        """
        Map property types to standardized categories (house, flat, or unknown).

        Parameters:
        -----------
        property_type_series : pd.Series
            A pandas Series containing property type values

        Returns:
        --------
        pd.Series
            A pandas Series with mapped property type categories
        """
        # Create a copy to avoid modifying the original
        property_type_copy = property_type_series.copy()

        # Convert to lower casing
        property_type_copy = property_type_copy.str.lower()

        # Create a mapping dictionary
        property_type_mapping = {
            "house": [
                "house",
                "new house land",
                "townhouse",
                "villa",
                "semi-detached",
                "terrace",
                "duplex",
            ],
            "flat": [
                "apartment unit flat",
                "studio",
                "new apartments off the plan",
                "penthouse",
            ],
        }

        # Create inverted mapping (property type -> category)
        inverted_property_type_mapping = {}
        for category, property_types in property_type_mapping.items():
            for prop_type in property_types:
                inverted_property_type_mapping[prop_type] = category

        # Map property types to categories
        house_flat_other = property_type_copy.map(inverted_property_type_mapping)

        # Fill NaN values with "unknown"
        house_flat_other = house_flat_other.fillna("unknown")

        return house_flat_other

    def extract_rental_price(self, rental_price_series):
        """
        Extract weekly rent from rental price strings.

        Parameters:
        -----------
        rental_price_series : pd.Series
            A pandas Series containing rental price strings

        Returns:
        --------
        pd.Series
            A pandas Series with weekly rent values (NaN for unknown frequencies)
        """
        # Create a copy to avoid modifying the original
        rental_price_copy = rental_price_series.copy()

        # Remove '$' and ',' from rental_price
        rental_price_copy = rental_price_copy.replace("[\$,]", "", regex=True).astype(
            str
        )

        # Convert to lowercase
        rental_price_copy = rental_price_copy.str.lower()

        # Remove spaces in rental_price
        rental_price_copy = rental_price_copy.str.replace(" ", "", regex=False)

        # Extract numeric value from rental_price (based on the first number found)
        price_value = rental_price_copy.str.extract(r"(\d+(?:\.\d+)?)")[0].astype(float)

        freq_keywords = [
            "pw",
            "perweek",
            "weekly",
            "p/w",
            "wk",
            "p.w.",
            "/wk",
            "/w",
            "/week",
            "p.w",
            "permonth",
            "pm",
            "calendar",
            "monthly",
            "calender",
            "percalendarmonth",
            "percalendermonth",
        ]

        # Extract frequency keyword after the number
        price_frequency = rental_price_copy.str.extract(
            r"(\d+(?:\.\d+)?)+(" + "|".join(freq_keywords) + ")", expand=False
        )[1]

        # Map known patterns to standardized categories
        frequency_mapping = {
            "pw": "weekly",
            "p.w.": "weekly",
            "perweek": "weekly",
            "weekly": "weekly",
            "p/w": "weekly",
            "wk": "weekly",
            "p.w": "weekly",
            "/wk": "weekly",
            "/w": "weekly",
            "/week": "weekly",
            "pm": "monthly",
            "permonth": "monthly",
            "calendar": "monthly",
            "calender": "monthly",
            "monthly": "monthly",
            "percalendarmonth": "monthly",
            "percalendermonth": "monthly",
        }

        price_frequency = price_frequency.map(frequency_mapping)

        # If price is purely numeric (digits and full stops), assume weekly
        numeric_mask = rental_price_copy.str.match(r"^[\d\.]+$")
        price_frequency.loc[numeric_mask & price_frequency.isna()] = "weekly"

        # Assign 'unknown' to unmatched entries
        price_frequency = price_frequency.fillna("unknown")

        # Convert to categorical type
        price_frequency = pd.Categorical(
            price_frequency, categories=["weekly", "monthly", "unknown"]
        )

        # Create weekly_rent based on price_frequency
        weekly_rent = pd.Series(index=rental_price_series.index, dtype=float)

        # Calculate weekly rent
        weekly_mask = price_frequency == "weekly"
        monthly_mask = price_frequency == "monthly"
        unknown_mask = price_frequency == "unknown"

        weekly_rent.loc[weekly_mask] = price_value.loc[weekly_mask]
        weekly_rent.loc[monthly_mask] = price_value.loc[monthly_mask] / 4
        weekly_rent.loc[unknown_mask] = None

        return weekly_rent

    def impute_by_property_type_mode(
        self, df, column_name, property_type_column="property_type"
    ):
        """
        Impute missing values in a column by using the mode for each property_type.

        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame containing the data
        column_name : str
            Name of the column to impute (e.g., 'bedrooms')
        property_type_column : str, optional
            Name of the property type column (default: 'property_type')

        Returns:
        --------
        pd.Series
            Series with imputed values
        """
        # Calculate mode for each property_type
        mode_by_type = df.groupby(property_type_column)[column_name].agg(
            lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        )

        # Get overall mode as fallback
        overall_mode = (
            df[column_name].mode()[0] if len(df[column_name].mode()) > 0 else None
        )

        # Create a copy of the column to avoid SettingWithCopyWarning
        result = df[column_name].copy()

        # Fill missing values based on property_type
        for prop_type in df[property_type_column].unique():
            mask = (df[property_type_column] == prop_type) & (df[column_name].isna())
            fill_value = mode_by_type.get(prop_type, overall_mode)
            if mask.sum() > 0:
                print(
                    f"Property type: {prop_type}, {column_name} imputed with {fill_value}"
                )
            if fill_value is not None:
                result.loc[mask] = fill_value

        return result
