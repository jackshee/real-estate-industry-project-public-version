#!/bin/bash

# POI Features Batch Processing Script - Part 2
# This script runs POI feature extraction for CSV files from missing_poi_4500.csv to missing_poi_7000.csv

# Set up logging
LOG_FILE="poi_batch_processing_part2.log"
echo "Starting POI batch processing Part 2 (4500-7000) at $(date)" | tee -a "$LOG_FILE"

# Activate virtual environment
#echo "Activating virtual environment..." | tee -a "$LOG_FILE"
#source /opt/anaconda3/envs/pyspark-env/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated: $VIRTUAL_ENV" | tee -a "$LOG_FILE"
else
    echo "ERROR: Failed to activate virtual environment" | tee -a "$LOG_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p data/processed/poi_features

# Process CSV files from 4500 to 7000
echo "Processing POI files 4500-7000..." | tee -a "$LOG_FILE"

# Define the range of files to process
start_num=4500
end_num=7000
step=500

current_file=0
total_files=$(((end_num - start_num) / step + 1))

for ((num=start_num; num<=end_num; num+=step)); do
    csv_file="data/raw/missing_poi/missing_poi_${num}.csv"
    
    # Check if file exists
    if [[ ! -f "$csv_file" ]]; then
        echo "WARNING: File $csv_file not found, skipping..." | tee -a "$LOG_FILE"
        continue
    fi
    
    current_file=$((current_file + 1))
    
    echo "Processing file $current_file/$total_files: $csv_file (number: $num)" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"
    
    # Run the POI extraction script
    python notebooks/api/fetch_osm_poi_features.py \
        --input-file "$csv_file" \
        --output-dir "data/processed/poi_features" \
        2>&1 | tee -a "$LOG_FILE"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Completed processing $csv_file at $(date)" | tee -a "$LOG_FILE"
    else
        echo "ERROR: Failed to process $csv_file at $(date)" | tee -a "$LOG_FILE"
        echo "Continuing with next file..." | tee -a "$LOG_FILE"
    fi
    
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    # Add a delay between files to be respectful to the API
    if [ $num -lt $end_num ]; then
        echo "Waiting 10 seconds before next file..." | tee -a "$LOG_FILE"
        sleep 10
    fi
done

echo "POI batch processing Part 2 (4500-7000) completed at $(date)" | tee -a "$LOG_FILE"

# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated" | tee -a "$LOG_FILE"

echo "Part 2 POI processing complete! Check $LOG_FILE for details." | tee -a "$LOG_FILE"
