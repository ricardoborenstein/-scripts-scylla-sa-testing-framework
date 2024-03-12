#!/bin/bash

# Check if a command-line argument is provided
if [ -n "$1" ]; then
    case $1 in
        aws)
            provider="aws"
            ;;
        gcp)
            provider="gcp"
            ;;
        *)
            echo "Invalid option. Please use 'aws' or 'gcp'."
            exit 1
            ;;
    esac
else
    # No command-line argument provided, prompt the user to choose a provider
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
fi

# Check if the provider is AWS
if [ "$provider" == "aws" ]; then
    cd $provider/cluster/
    python3 configure_vars.py
    # Initialize Terraform (download providers, etc.)
    terraform init
    # Apply the Terraform configuration
    terraform apply
    cd ../ansible_install
    python3 configure_vars_ansible.py
    # Install Scylla
    set -e
    ansible-playbook install_scylla.yml
    ansible-playbook get_monitoring_config.yml
    ansible-playbook install_monitoring.yml
    ansible-playbook install_loader.yml
    set +e
    echo "System is ready for testing."
    echo -e "If you want to run benchmark now, start by loading data:\n cd ${PWD}; ansible-playbook benchmark_start_load.yml;"
# Check if the provider is GCP
elif [ "$provider" == "gcp" ]; then
    cd $provider/cluster/
    python3 configure_vars.py
    # Initialize Terraform (download providers, etc.)
    terraform init
    # Apply the Terraform configuration
    terraform apply
fi

# Optionally, you can configure provider-specific credentials here or through environment variables
