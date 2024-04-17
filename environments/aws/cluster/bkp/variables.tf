#
# Set the following variables (mandatory)
#

# AWS credentials file
variable "path_to_aws_cred_file" {
  description = "AWS credentials location"
  type        = string
  default     = "/Users/ricardo/.aws/credentials"
}

# AWS credentials file
variable "aws_creds_profile" {
  description = "AWS credentials profile"
  type        = string
  default     = "DevOpsAccessRole"
}

# SSH private key for EC2 instance access
variable "ssh_private_key" {
  description = "SSH private key location for EC2 instance access"
  type        = string
  default     = "/Users/ricardo/Downloads/ricardo-terraform.pem"
}

variable "aws_key_pair_name" {
  description = "Key pair name in AWS"
  type        = string
  default     = "ricardo-terraform"
}

variable "aws_region" {
  description = "Key pair name in AWS"
  type        = string
  default     = "us-east-1"
}

# Scylla instance type
variable "scylla_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "i4i.2xlarge"
}

# Loader instance type
variable "loader_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "m5.2xlarge"
}

# Amazon Machine Image (AMI) ID
variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-053053586808c3e70"
}

# Scylla (AMI) ID
variable "scylla_ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0d5a0ef6e53048c88"
}


variable "gpg_keys_scylla" {
  description = "gpg key for scylla"
  type        = string
  default     = "d0a112e067426ab2"
}
# Virtual Private Cloud (VPC) IP range
variable "custom_vpc" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}
# SUBNET Count
variable "subnet_count" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "1"   
}

# Amazon Machine Image (AMI) Username
variable "instance_username" {
  description = "username for the AMI"
  type        = string
  default     = "ubuntu"
}


# Monitoring instance type
variable "monitoring_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "m5.2xlarge"
}


################################################

#
# The following variables are not required to be modified to run the demo
# but you can still modify them if you want to try a different setup
#

# Number of threads for the Cassandra stress tool
variable "num_threads" {
  description = "Number of threads for the Cassandra stress tool"
  type        = string
  default     = "128"
}

# Total number of operations to run
variable "num_of_ops" {
  description = "Total number of operations to run"
  type        = string
  default     = "46B"
}

# Throttling for the Cassandra stress tool
variable "throttle" {
  description = "Throttling for the Cassandra stress tool (in ops/sec)"
  type        = string
  default     = "100000/s"
}

# Environment name
variable "custom_name" {
  description = "Name for the ScyllaDB Cloud environment"
  type        = string
  default     = "Ricardo-Benchmark"
}


# Number of ScyllaDB  instances to create
variable "scylla_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "3"
}

# Number of Loaders instances to create
variable "loader_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "1"
}

