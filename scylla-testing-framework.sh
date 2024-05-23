#!/bin/bash

# Function to update scylla_version in YAML file based on cloud provider
update_scylla_version() {
    local provider="$1"
    local yaml_file="variables.yml"  # specify your yaml file path

    # Ensure the file exists
    if [ ! -f "$yaml_file" ]; then
        echo "Error: YAML file does not exist at the specified path: $yaml_file"
        return 1
    fi

    # Extract the current version from the YAML file
    local current_version=$(grep "scylla_version:" $yaml_file | awk -F\" '{print $2}')
    
    # Check extraction success
    if [ -z "$current_version" ]; then
        echo "Error: Failed to extract scylla_version from $yaml_file"
        return 1
    else
        echo "Current version extracted: $current_version"
    fi

    local formatted_version="$current_version"
    case "$provider" in
        "aws")
            formatted_version="${current_version//-/.}"  # Ensure format uses dots
            ;;
        "gcp")
            formatted_version="${current_version//./-}"  # Ensure format uses underscores
            ;;
        *)
            echo "Unsupported provider: $provider"
            return 1
            ;;
    esac

    # Check if reformatting is needed
    if [ "$current_version" == "$formatted_version" ]; then
        echo "No update needed, scylla_version already formatted for $provider."
    else
        # Update the file using sed according to OS
        echo "Updating scylla_version for $provider..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/scylla_version: \"$current_version\"/scylla_version: \"$formatted_version\"/" $yaml_file
        else
            sed -i "s/scylla_version: \"$current_version\"/scylla_version: \"$formatted_version\"/" $yaml_file
        fi
        echo "scylla_version updated from $current_version to $formatted_version."
    fi

    # Display updated line for verification
    grep "scylla_version:" $yaml_file
}


# Function to perform AWS setup
aws_setup() {
    
    set -e
    update_scylla_version "aws" 
    #export AWS_PROFILE=DevOpsAccessRole
    cd aws/cluster/
    #python3 configure_vars.py
    python3 dynamic_aws_setup.py
    # Initialize Terraform (download providers, etc.)
    terraform init
    # Apply the Terraform configuration
    terraform apply -auto-approve
    sleep 60
    set +e
    #aws_config()
    
    echo "System is ready for testing."
}

aws_config(){
    sleep 5
    cd aws/ansible_install
    python3 configure_vars_ansible.py
    # Install Scylla
    set -e
    ansible-playbook wait_for_seed.yml
    ansible-playbook start_other_dcs.yml
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
    python3 aws_configure_stress_profile.py
    # Load data and run benchmark
    cd ../aws/ansible_install
    echo "Starting benchmark..."
    ansible-playbook benchmark_start_load.yml
    # Add additional benchmark commands here
}

aws_destroy() {
    set -e
    #export AWS_PROFILE=DevOpsAccessRole
    cd aws/cluster/
    terraform destroy --auto-approve
}


# Function to perform AWS setup
gcp_setup() {
    set -e
    update_scylla_version "gcp" 
    cd gcp/cluster/
    #python3 configure_vars.py
    python3 dynamic_gcp_setup.py
    # Initialize Terraform (download providers, etc.)
    terraform init
    # Apply the Terraform configuration
    terraform apply -auto-approve
    set +e
    #gcp_config()
    sleep 60
    echo "System is ready for testing."
}

# Function to perform AWS benchmark
gcp_benchmark() {
    cd ./benchmark/
    echo "Configuring stress profile"
    python3 config_ycsb.py
    # Load data and run benchmark
    cd ../gcp/ansible_install
    echo "Starting benchmark..."
    ansible-playbook ycsb.yml
    # Add additional benchmark commands here
}

gcp_config(){
    sleep 5
    cd gcp/cluster/
    cd ../ansible_install
    python3 configure_vars_ansible.py
    # Install Scylla
    set -e
    ansible-playbook wait_for_seed.yml
    ansible-playbook start_other_dcs.yml
    ansible-playbook start_nonseed.yml
    ansible-playbook get_monitoring_config.yml
    ansible-playbook install_monitoring.yml
    ansible-playbook install_loader.yml
    set +e
}

gcp_destroy() {
    set -e
    cd gcp/cluster/
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
        case $operation in
            "setup") gcp_setup ;;
            "config") gcp_config ;;
            "benchmark") gcp_benchmark ;;
            "destroy") gcp_destroy ;;
        esac
    else
        echo "Unsupported provider: $provider"
        exit 1
    fi
}

# Process the provided arguments
process_arguments $1 $2