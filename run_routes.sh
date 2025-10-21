#!/bin/bash

# Routes Batch Processing Script for Wayback Listings
# This script calculates routing distances from wayback property listings to POI locations

# Set up logging
LOG_FILE="routes_wayback_processing.log"
echo "Starting routes wayback processing at $(date)" | tee -a "$LOG_FILE"

# Activate virtual environment
echo "Activating virtual environment..." | tee -a "$LOG_FILE"
source venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated: $VIRTUAL_ENV" | tee -a "$LOG_FILE"
else
    echo "ERROR: Failed to activate virtual environment" | tee -a "$LOG_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR="data/processed/routes_ptv"
mkdir -p "$OUTPUT_DIR"

# Define POI file (adjust this path if needed)
POI_FILE="data/landing/ptv/public_transport_stops.geojson"

# Check if POI file exists
if [[ ! -f "$POI_FILE" ]]; then
    echo "ERROR: POI file not found: $POI_FILE" | tee -a "$LOG_FILE"
    echo "Please update the POI_FILE variable in this script with the correct path" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Using POI file: $POI_FILE" | tee -a "$LOG_FILE"

# Initialize API key rotation
api_key_num=1
execution_count=0

# Process all batch files in missing_routes_wayback
INPUT_DIR="data/raw/missing_routes_remain"
echo "Processing route files from $INPUT_DIR..." | tee -a "$LOG_FILE"

# Get list of all batch CSV files
batch_files=($(ls -1 "$INPUT_DIR"/batch_*.csv 2>/dev/null | sort))

if [ ${#batch_files[@]} -eq 0 ]; then
    echo "ERROR: No batch files found in $INPUT_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Found ${#batch_files[@]} batch files to process" | tee -a "$LOG_FILE"

current_file=0
total_files=${#batch_files[@]}

for csv_file in "${batch_files[@]}"; do
    current_file=$((current_file + 1))
    
    # Extract batch number from filename
    batch_name=$(basename "$csv_file" .csv)
    
    echo "========================================" | tee -a "$LOG_FILE"
    echo "Processing file $current_file/$total_files: $csv_file" | tee -a "$LOG_FILE"
    echo "Batch: $batch_name" | tee -a "$LOG_FILE"
    echo "Using ORS_API_KEY${api_key_num} (execution #$execution_count)" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"
    
    # Run the routes extraction script
    python scripts/api/fetch_ors_routes.py \
        --input-listings-file "$csv_file" \
        --input-poi-file "$POI_FILE" \
        --output-dir "$OUTPUT_DIR" \
        --max-km 3.0 \
        --k-nearest 10 \
        --api-key "ORS_API_KEY${api_key_num}" \
        2>&1 | tee -a "$LOG_FILE"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Completed processing $csv_file at $(date)" | tee -a "$LOG_FILE"
    else
        echo "ERROR: Failed to process $csv_file at $(date)" | tee -a "$LOG_FILE"
        echo "Continuing with next file..." | tee -a "$LOG_FILE"
    fi
    
    # Increment execution count and API key number
    execution_count=$((execution_count + 1))
    api_key_num=$((api_key_num + 1))
    
    echo "Completed execution #${execution_count}. Next API key will be ORS_API_KEY${api_key_num}" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    # Add a delay between files to be respectful to the API
    if [ $current_file -lt $total_files ]; then
        echo "Waiting 15 seconds before next file..." | tee -a "$LOG_FILE"
        sleep 15
    fi
done

echo "========================================" | tee -a "$LOG_FILE"
echo "Routes wayback processing completed at $(date)" | tee -a "$LOG_FILE"
echo "Processed $current_file out of $total_files files" | tee -a "$LOG_FILE"

# Count successful outputs
output_files=($(ls -1 "$OUTPUT_DIR"/*.csv 2>/dev/null))
echo "Generated ${#output_files[@]} output files in $OUTPUT_DIR" | tee -a "$LOG_FILE"

# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated" | tee -a "$LOG_FILE"

echo "Routes wayback processing complete! Check $LOG_FILE for details." | tee -a "$LOG_FILE"

