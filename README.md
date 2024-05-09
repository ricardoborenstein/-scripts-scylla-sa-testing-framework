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
- AWS CLI configured (for AWS operations)
- GCP SDK configured (for GCP operations)

## Ansible Requirements

Install the necessary Ansible roles using the following commands:

```bash
ansible-galaxy role install geerlingguy.swap
ansible-galaxy role install mrlesmithjr.mdadm
```
## Python Environment Setup
Before running the script, set up a Python virtual environment and install the required packages:
```bash
python3 -m venv venv
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

### Configuration Files
variables.yml: Contains configuration variables like scylla_version. Ensure this file is configured properly before running the script.