#!/bin/bash

# Shell script to run isochrone fetching for all files in driving directory with API key rotation
# Loops through all missing_isochrones_*.csv files in data/raw/missing_isochrones/driving/
# API key starts at 16 and increments by 1 every 5 executions

# Activate virtual environment
source venv/bin/activate

# Initialize counters
api_key_num=1
execution_count=0
# Get list of all missing_isochrones_*.csv files in the driving directory
driving_dir="data/raw/missing_isochrones_remain/driving"
files=($(ls ${driving_dir}/batch_*.csv | sort -V))

echo "Found ${#files[@]} files to process in ${driving_dir}"

# Loop through all files in the driving directory
for file in "${files[@]}"; do
    # Extract just the filename for display
    filename=$(basename "$file")
    
    # Increment API key number every 5 executions
    if [ $((execution_count % 5)) -eq 0 ] && [ $execution_count -gt 0 ]; then
        api_key_num=$((api_key_num + 1))
    fi
    
    echo "Processing ${filename} with APIKEY${api_key_num} (execution #$((execution_count + 1)))"
    
    # Run the Python script
    python scripts/api/fetch_ors_isochrones.py \
        --input-file "${file}" \
        --profile driving \
        --api-key "APIKEY${api_key_num}"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Successfully processed ${filename}"
    else
        echo "Error processing ${filename}"
    fi
    
    # Increment execution count
    execution_count=$((execution_count + 1))
    
    echo "Completed execution #${execution_count}. Next API key will be APIKEY${api_key_num} (after 5 more executions)"
    echo "---"
done

echo "All batch processing completed!"
echo "Total executions: ${execution_count}"
