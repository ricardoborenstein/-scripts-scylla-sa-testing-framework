#!/bin/bash

echo "Select your cloud provider:"
echo "1) AWS"
echo "2) GCP"
read -p "Provider (1/2): " provider_choice

case $provider_choice in
    1)
        provider="aws"
        ;;
    2)
        provider="gcp"
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac

if provider == "aws"; do
    

# Navigate to the specific provider directory
cd terraform-config/$provider/cluster/

# Optionally, you can configure provider-specific credentials here or through environment variables

# Initialize Terraform (download providers, etc.)
terraform init

# Apply the Terraform configuration
terraform apply

# You can also add options to pass specific variables or configurations
