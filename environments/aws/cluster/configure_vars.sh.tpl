#!/bin/bash

# Define file paths
CFG_FILE="./../../variables.cfg"
TEMPLATE_FILE="./variables.tf.tpl"
OUTPUT_FILE="./variables.tf1"

# Copy the template to the output file
cp "$TEMPLATE_FILE" "$OUTPUT_FILE"

# Process each variable in the configuration file
while IFS=' = ' read -r key value; do
    # Remove quotes around the value
    trimmed_value="${value%\"}"
    trimmed_value="${trimmed_value#\"}"

    # Use sed to safely handle replacement in the output file
    # Escape forward slashes in the replacement value
    escaped_value=$(printf '%s\n' "$trimmed_value" | sed 's:[][\/.^$*]:\\&:g')
    
    # Determine the correct sed command based on the operating system
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # MacOS requires an empty extension with -i option
        sed -i '' "/variable \"$key\"/,/}/s/default[[:space:]]*=.*/default     = \"$escaped_value\"/" "$OUTPUT_FILE"
    else
        # Linux
        sed -i "/variable \"$key\"/,/}/s/default[[:space:]]*=.*/default     = \"$escaped_value\"/" "$OUTPUT_FILE"
    fi
done < "$CFG_FILE"

echo "Variables updated in $OUTPUT_FILE"