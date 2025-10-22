# MAST30034 Applied Data Science - Real Estate Analysis Project

A comprehensive data science project analysing Victorian rental property markets through web scraping, feature engineering, machine learning, and spatial analysis.

## 🏠 Project Overview

This project analyses rental property markets across Victoria, Australia, combining web-scraped property data with economic indicators, demographic information, and spatial amenities to predict rental prices and assess suburb liveability.

## 📁 Repository Structure

```
project2/
├── data/                           # Data storage organised by processing stage
│   ├── landing/                    # Raw scraped data from Domain.com.au
│   ├── curated/                    # Cleaned and processed datasets
│   ├── processed/                  # Feature-engineered data
│   └── analysis/                   # Final analysis outputs
├── notebooks/                      # Jupyter notebooks for analysis
│   ├── 0_data_download.ipynb      # Data collection and initial processing
│   ├── 1_feature_engineer.ipynb   # Feature engineering and data preparation
│   ├── 1_model_xgboost_external.ipynb  # XGBoost model training and evaluation
│   ├── 1_preprocess_domain.ipynb  # Domain data preprocessing
│   ├── 2_feature_engineer.ipynb  # Advanced feature engineering
│   ├── 2_lasso_var.ipynb          # LASSO feature selection and VAR forecasting
│   ├── 2_preprocess_forecast.ipynb  # Forecast data preprocessing
│   ├── 2_sar_analysis.ipynb      # Spatial Autoregression analysis
│   ├── 3_affordability.ipynb     # Housing affordability analysis
│   ├── 3_liveability.ipynb      # Suburb liveability scoring
│   └── summary_notebook.ipynb    # Project summary and conclusions
├── scraping/                      # Web scraping tools
│   ├── domain_scraper/            # Scrapy-based Domain.com.au scraper
│   └── functions/                 # Utility functions for scraping
├── scripts/                       # Python scripts for data processing
│   ├── api/                       # API integration scripts
│   └── *.py                       # Data pipeline scripts
├── utils/                         # Utility modules
├── models/                        # Trained machine learning models
├── figures/                       # Generated visualizations
├── geovisualization/             # Geographic visualizations
├── requirements.txt              # Python dependencies
├── setup_mac.sh                  # macOS setup script
├── setup_windows.bat             # Windows setup script
└── README.md                     # This file
```

## 🚀 Repository Setup

### 1. Environment Setup

**For macOS/Linux:**
```bash
# Navigate to the project directory
cd "MAST30034 Applied Data Science/project2"

# Run the setup script
chmod +x setup_mac.sh
./setup_mac.sh
```

**For Windows:**
```cmd
REM Navigate to the project directory
cd "C:\path\to\MAST30034 Applied Data Science\project2"

REM Run the setup script
setup_windows.bat
```

**Manual Setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Data Pipeline Setup

The project requires several external data sources and API keys:

1. **Domain.com.au scraping**: Automated via Scrapy spiders
2. **OpenRouteService API**: For isochrone and routing analysis
3. **Census data**: Downloaded from ABS
4. **School data**: Scraped from government sources

## 📊 Notebook Execution Order

Execute notebooks in the following sequence for complete analysis:

### Phase 1: Data Collection & Initial Processing
1. **`0_data_download.ipynb`** - Downloads and processes raw data from various sources including Domain.com.au, census data, and economic indicators.

### Phase 2: Feature Engineering & Model Development
2. **`1_preprocess_domain.ipynb`** - Cleans and preprocesses scraped rental property data from Domain.com.au.
3. **`1_feature_engineer.ipynb`** - Creates initial features from property listings and geographic data.
4. **`2_feature_engineer.ipynb`** - Performs advanced feature engineering including POI analysis and spatial features.
5. **`2_lasso_var.ipynb`** - Uses LASSO regression for feature selection and VAR models for economic forecasting.
6. **`2_preprocess_forecast.ipynb`** - Prepares forecast data for model training and evaluation.

### Phase 3: Modeling & Analysis
7. **`1_model_xgboost_external.ipynb`** - Trains and evaluates XGBoost models for rental price prediction.
8. **`2_sar_analysis.ipynb`** - Performs Spatial Autoregression analysis to account for spatial dependencies.

### Phase 4: Policy Analysis
9. **`3_affordability.ipynb`** - Analyzes housing affordability across Victorian suburbs using income-to-rent ratios.
10. **`3_liveability.ipynb`** - Creates comprehensive liveability scores based on amenities, transport, and quality of life factors.

### Phase 5: Summary
11. **`summary_notebook.ipynb`** - Provides project summary, key findings, and conclusions.

## 📈 Notebook Descriptions

- **`0_data_download.ipynb`**: Downloads and processes raw data from various sources including Domain.com.au, census data, and economic indicators.
- **`1_preprocess_domain.ipynb`**: Cleans and preprocesses scraped rental property data from Domain.com.au.
- **`1_feature_engineer.ipynb`**: Creates initial features from property listings and geographic data.
- **`1_model_xgboost_external.ipynb`**: Trains and evaluates XGBoost models for rental price prediction.
- **`2_feature_engineer.ipynb`**: Performs advanced feature engineering including POI analysis and spatial features.
- **`2_lasso_var.ipynb`**: Uses LASSO regression for feature selection and VAR models for economic forecasting.
- **`2_preprocess_forecast.ipynb`**: Prepares forecast data for model training and evaluation.
- **`2_sar_analysis.ipynb`**: Performs Spatial Autoregression analysis to account for spatial dependencies.
- **`3_affordability.ipynb`**: Analyzes housing affordability across Victorian suburbs using income-to-rent ratios.
- **`3_liveability.ipynb`**: Creates comprehensive liveability scores based on amenities, transport, and quality of life factors.
- **`summary_notebook.ipynb`**: Provides project summary, key findings, and conclusions.

## 🛠️ Key Technologies

### Data Collection
- **Scrapy**: Professional web scraping framework for Domain.com.au
- **OpenRouteService API**: Geographic routing and isochrone analysis
- **ABS Census API**: Demographic and economic data

### Data Science Stack
- **pandas/numpy**: Data manipulation and numerical computing
- **scikit-learn**: Machine learning algorithms and preprocessing
- **XGBoost**: Gradient boosting for price prediction
- **statsmodels**: Statistical modeling and VAR analysis
- **geopandas**: Geospatial data analysis

### Visualization
- **matplotlib/seaborn**: Statistical visualizations
- **plotly**: Interactive maps and charts
- **folium**: Geographic mapping

## 📊 Project Outputs

### Models
- **XGBoost rental price predictor**: Trained model for price prediction
- **VAR economic forecasts**: Economic indicator predictions
- **SAR spatial models**: Spatial dependency analysis

### Analysis Results
- **Affordability rankings**: Suburb-level affordability analysis
- **Liveability scores**: Multi-dimensional quality of life metrics
- **Feature importance**: Key drivers of rental prices

### Visualizations
- **Geographic maps**: Spatial distribution of prices and amenities
- **Time series**: Economic trends and forecasts
- **Statistical plots**: Model performance and feature analysis

## 🔧 Configuration

### API Keys Required
- OpenRouteService API key for geographic analysis
- Domain.com.au access (respects rate limits)

### Data Storage
- Raw data: `data/landing/`
- Processed data: `data/processed/`
- Final outputs: `data/analysis/`

## 📚 Dependencies

See `requirements.txt` for complete dependency list. Key packages include:
- pandas, numpy, scikit-learn
- xgboost, statsmodels
- geopandas, folium
- scrapy, requests
- matplotlib, seaborn, plotly

## 🎯 Project Goals

1. **Predict rental prices** using machine learning models
2. **Identify key factors** driving rental market dynamics
3. **Assess affordability** across Victorian suburbs
4. **Create liveability metrics** for urban planning insights
5. **Provide policy recommendations** for housing market analysis

## 📄 License

This project is for educational purposes as part of MAST30034 Applied Data Science course at the University of Melbourne.

---

**Note**: This project respects website terms of service and implements appropriate rate limiting for data collection.