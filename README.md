# Cloud Scylla Deployment Script

This repository contains a script for deploying and managing ScyllaDB instances on cloud platforms such as AWS and GCP. The script supports various operations including setup, configuration, benchmarking, and destruction of cloud resources.

## Features

- **Flexible Version Management**: Dynamically update Scylla version based on cloud provider specifications.
- **Automated Cloud Operations**: Automate the setup and teardown of ScyllaDB clusters with integrated Terraform and Ansible playbooks.
- **Benchmarking Tools**: Facilitate stress testing and benchmarking of the ScyllaDB instances.

## Prerequisites

- Bash
- Python 3
- Terraform
- Ansible
- AWS CLI configured (for AWS operations) and key pair available in the region.
- GCP SDK configured (for GCP operations)

## GCP Auth

```bash
gcloud auth application-default login
```

## Ansible Requirements

Install the necessary Ansible roles using the following commands:

```bash
ansible-galaxy role install geerlingguy.swap
ansible-galaxy role install mrlesmithjr.mdadm
```
## Python Environment Setup
Before running the script, set up a Python virtual environment and install the required packages:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Cloning the Repository

When cloning the repository, also clone the submodules:


```bash
git clone --recurse-submodules https://github.com/ricardoborenstein/scylla-sa-testing-framework.git
```


## Usage
The main script is designed to be executed with two arguments specifying the cloud provider and the desired operation. Here are the operations you can perform:

### General Syntax
```bash
./scylla-testing-framework.sh [provider] [operation]
```
#### Supported Providers
* aws: Amazon Web Services
* gcp: Google Cloud Platform
#### Supported Operations
* setup: Initialize and configure the cloud infrastructure and ScyllaDB instances.
* config: Reconfigure existing ScyllaDB instances.
* benchmark: Perform benchmarks on the ScyllaDB instances.
* destroy: Remove all cloud resources associated with the ScyllaDB instances.
#### Examples
To set up Scylla on AWS:

```bash
./scylla-testing-framework.sh aws setup
```
To destroy the Scylla environment on GCP:

``` bash
./scylla-testing-framework.sh gcp destroy
```

To start the Benchmark on GCP:

``` bash
./scylla-testing-framework.sh gcp benchmark
```

### Configuration Files
`variables.yml`
This YAML file contains all the configurable parameters required by the deployment script. Adjust the settings in variables.yml to tailor the deployment to your needs. Below is an example highlighting some of the key parameters:


```yaml
cluster_name: "Ricardo Testing"
scylla_version: "2024.1.4"
gcp_project_id: "skilled-adapter-452" # Only relevant for GCP
regions:
  "us-east-1": 
    nodes: 3
    scylla_node_type: "i4i.large"
    disk_size_gb: 700 # Only relevant for GCP
    loaders: 3
    loaders_type: "m5.large"
    cidr: "10.0.0.0/16"
    az_mode: "single-az"
key_pair_name: "ricardo-terraform" # Only relevant for AWS
path_to_key: "~/Downloads/ricardo-terraform.pub"
monitoring_type: "m5.large"
cassandra-stress:
  num_threads: 64
  num_of_ops: "1000000"
  throttle: "21000/s"
  ratio: "1:4"
  template: "ott-audio-streaming"
```

#### Setting Up Multiple Regions
The regions section of the`variables.yml` file allows you to configure multiple regions for deployment. Each region can have its own set of configurations such as the number of nodes, node type, disk size, and networking settings. This flexibility helps in customizing the deployment based on geographic requirements and resource availability.

