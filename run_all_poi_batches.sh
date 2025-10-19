#!/bin/bash

# Master script to run all 28 POI batch processing scripts in series
# This script processes all POI batches directly without relying on separate batch scripts

echo "Starting all 28 POI batch processing scripts in series..."
echo "Each batch will run one after another."

# Get the current directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

# Set up main logging
MAIN_LOG_FILE="poi_batch_processing_remain_all.log"
echo "Starting POI batch processing for all batches at $(date)" | tee -a "$MAIN_LOG_FILE"

# Activate virtual environment
echo "Activating virtual environment..." | tee -a "$MAIN_LOG_FILE"
source venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated: $VIRTUAL_ENV" | tee -a "$MAIN_LOG_FILE"
else
    echo "ERROR: Failed to activate virtual environment" | tee -a "$MAIN_LOG_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p data/processed/poi_features_remain

# Run all 28 batch scripts in series
for i in {1..28}; do
    # Format the batch number with leading zeros
    batch_num=$(printf "%04d" $i)
    csv_file="data/raw/missing_poi_remain/batch_${batch_num}.csv"
    log_file="poi_batch_processing_remain_part${i}.log"
    
    echo "==========================================" | tee -a "$MAIN_LOG_FILE"
    echo "Starting batch $i/28..." | tee -a "$MAIN_LOG_FILE"
    echo "Processing: $csv_file (batch: $batch_num)" | tee -a "$MAIN_LOG_FILE"
    echo "Started at: $(date)" | tee -a "$MAIN_LOG_FILE"
    echo "==========================================" | tee -a "$MAIN_LOG_FILE"
    
    # Check if file exists
    if [[ ! -f "$csv_file" ]]; then
        echo "WARNING: File $csv_file not found, skipping..." | tee -a "$MAIN_LOG_FILE"
        continue
    fi
    
    # Run the POI extraction script
    echo "Processing POI remain files batch $batch_num..." | tee -a "$log_file"
    python scripts/api/fetch_osm_poi_features.py \
        --input-file "$csv_file" \
        --output-dir "data/processed/poi_features_remain" \
        2>&1 | tee -a "$log_file"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Completed processing $csv_file at $(date)" | tee -a "$MAIN_LOG_FILE"
        echo "SUCCESS: Completed processing $csv_file at $(date)" >> "$log_file"
    else
        echo "ERROR: Failed to process $csv_file at $(date)" | tee -a "$MAIN_LOG_FILE"
        echo "ERROR: Failed to process $csv_file at $(date)" >> "$log_file"
        echo "Continuing with next batch..." | tee -a "$MAIN_LOG_FILE"
    fi
    
    echo "POI batch processing Batch $i (batch $batch_num) completed at $(date)" >> "$log_file"
    echo "Batch $i POI remain processing complete! Check $log_file for details." >> "$log_file"
    
    echo ""
    echo "Waiting 5 seconds before starting next batch..." | tee -a "$MAIN_LOG_FILE"
    sleep 5
done

# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated" | tee -a "$MAIN_LOG_FILE"

echo "==========================================" | tee -a "$MAIN_LOG_FILE"
echo "All 28 batches have been completed!" | tee -a "$MAIN_LOG_FILE"
echo "Finished at: $(date)" | tee -a "$MAIN_LOG_FILE"
echo "==========================================" | tee -a "$MAIN_LOG_FILE"
echo ""
echo "Log files to check for details:" | tee -a "$MAIN_LOG_FILE"
for i in {1..28}; do
    echo "  - poi_batch_processing_remain_part${i}.log" | tee -a "$MAIN_LOG_FILE"
done
echo "  - $MAIN_LOG_FILE (main log)" | tee -a "$MAIN_LOG_FILE"