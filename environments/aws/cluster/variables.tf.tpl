#
# Set the following variables (mandatory)
#

# AWS credentials file
variable "aws_creds" {
  description = "AWS credentials location"
  type        = string
  default     = "{{ path_to_aws_cred_file }}"
}

# AWS credentials file
variable "aws_creds_profile" {
  description = "AWS credentials profile"
  type        = string
  default     = "{{ aws_creds_profile }}"
}

# SSH private key for EC2 instance access
variable "ssh_private_key" {
  description = "SSH private key location for EC2 instance access"
  type        = string
  default     = "{{ aws_ssh_private_key }}"
}

variable "aws_key_pair_name" {
  description = "Key pair name in AWS"
  type        = string
  default     = "{{ aws_key_pair_name }}"
}

variable "aws_region" {
  description = "Key pair name in AWS"
  type        = string
  default     = "{{ aws_region }}"
}

# Scylla instance type
variable "scylla_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "{{ scylla_instance_type }}"
}

# Loader instance type
variable "loader_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "{{ loader_instance_type }}"
}

# Amazon Machine Image (AMI) ID
variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "{{ ami }}"
}

# Virtual Private Cloud (VPC) IP range
variable "custom_vpc" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "{{ CIDR }}"
}
# SUBNET Count
variable "subnet_count" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "{{ subnet_count }}"   
}

# Amazon Machine Image (AMI) Username
variable "instance_username" {
  description = "username for the AMI"
  type        = string
  default     = "{{ instance_username }}"
}


# Monitoring instance type
variable "monitoring_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "{{ monitoring_instance_type }}"
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
  default     = "{{ num_threads }}"
}

# Total number of operations to run
variable "num_of_ops" {
  description = "Total number of operations to run"
  type        = string
  default     = "{{ num_of_ops }}"
}

# Throttling for the Cassandra stress tool
variable "throttle" {
  description = "Throttling for the Cassandra stress tool (in ops/sec)"
  type        = string
  default     = "{{ throttle }}"
}

# Environment name
variable "custom_name" {
  description = "Name for the ScyllaDB Cloud environment"
  type        = string
  default     = "{{ custom_name }}"
}


# Number of ScyllaDB  instances to create
variable "scylla_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "{{ scylla_node_count }}"
}

# Number of Loaders instances to create
variable "loader_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "{{ loader_node_count }}"
}

