#!/bin/bash

# Directory containing input files
INPUT_DIR="data/raw/missing_coordinates"
OUTPUT_DIR="data/processed/coordinates"
ADDRESS_COLUMN="address"

# Counter for API keys
api_key_counter=2

# Loop through all CSV files in the input directory
for input_file in "$INPUT_DIR"/*.csv; do
    # Get the base filename without path
    filename=$(basename "$input_file")
    
    # Extract the base name without extension
    base_name="${filename%.csv}"
    
    # Construct output filename
    output_file="${OUTPUT_DIR}/${base_name}_geocoded.csv"
    
    # Check if output file already exists
    if [ -f "$output_file" ]; then
        echo "Skipping $filename - output file already exists"
        continue
    fi
    
    # Construct API key name
    api_key="ORS_API_KEY${api_key_counter}"
    
    echo "Processing $filename with $api_key..."
    
    # Run the Python script
    python notebooks/api/fetch_coordinates.py \
        --input-file "$input_file" \
        --api-key "$api_key" \
        --address-column "$ADDRESS_COLUMN"
    
    # Increment API key counter
    ((api_key_counter++))
done

echo "Geocoding complete!"

