#!/bin/bash

# Function to perform AWS setup
aws_setup() {
    set -e
    export AWS_PROFILE=DevOpsAccessRole
    cd aws/cluster/
    python3 configure_vars.py
    # Initialize Terraform (download providers, etc.)
    terraform init
    # Apply the Terraform configuration
    # Check if Terraform apply is needed
    # terraform plan -detailed-exitcode
    # exitcode=$?
    # if [ $exitcode -eq 2 ]; then
    #     # Apply the Terraform configuration if changes are detected
    #     echo "Applying Terraform changes..."
    #     terraform apply -auto-approve
    # else
    #     echo "No Terraform changes detected, skipping apply."
    # fi
    terraform apply -auto-approve
    sleep 5
    cd ../ansible_install
    python3 configure_vars_ansible.py
    # Install Scylla
    set -e
    ansible-playbook restart_nonseed.yml
    ansible-playbook get_monitoring_config.yml
    ansible-playbook install_monitoring.yml
    ansible-playbook install_loader.yml
    set +e
    echo "System is ready for testing."
}

aws_config(){
    sleep 5
    cd aws/ansible_install
    python3 configure_vars_ansible.py
    # Install Scylla
    set -e
    ansible-playbook restart_nonseed.yml
    ansible-playbook get_monitoring_config.yml
    ansible-playbook install_monitoring.yml
    ansible-playbook install_loader.yml
    set +e
    echo "System is ready for testing."
}


# Function to perform AWS benchmark
aws_benchmark() {
    cd ./benchmark/
    echo "Configuring stress profile"
    python3 configure_stress_profile.py
    # Load data and run benchmark
    cd ../aws/ansible_install
    echo "Starting benchmark..."
    ansible-playbook benchmark_start_load.yml
    # Add additional benchmark commands here
}

aws_destroy() {
    set -e
    export AWS_PROFILE=DevOpsAccessRole
    cd aws/cluster/
    terraform destroy --auto-approve
}
# Main logic to process arguments
process_arguments() {
    if [[ -n "$1" && -n "$2" ]]; then
        provider="$1"
        operation="$2"
    else
        # If insufficient arguments are provided, prompt for them
        echo "Select your cloud provider:"
        echo "1) AWS"
        echo "2) GCP"
        read -p "Provider (1/2): " provider_choice

        case $provider_choice in
            1) provider="aws" ;;
            2) provider="gcp" ;;
            *) echo "Invalid option."; exit 1 ;;
        esac

        echo "Select an operation:"
        echo "1) Setup"
        echo "2) Configure"
        echo "3) Benchmark"
        echo "4) Destroy"
        read -p "Operation (1/2/3/4): " operation_choice

        case $operation_choice in
            1) operation="setup" ;;
            2) operation="configure" ;;
            3) operation="benchmark" ;;
            4) operation="destroy" ;;
            *) echo "Invalid operation."; exit 1 ;;
        esac
    fi

    execute_operation
}

execute_operation() {
    if [ "$provider" == "aws" ]; then
        case $operation in
            "setup") aws_setup ;;
            "config") aws_config ;;
            "benchmark") aws_benchmark ;;
            "destroy") aws_destroy ;;
            *) echo "Invalid AWS operation."; exit 1 ;;
        esac
    elif [ "$provider" == "gcp" ]; then
        # Assuming future GCP-related operations might be added
        echo "GCP operations not yet implemented."
    else
        echo "Unsupported provider: $provider"
        exit 1
    fi
}

# Process the provided arguments
process_arguments $1 $2