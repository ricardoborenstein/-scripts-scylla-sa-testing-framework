#
# Set the following variables (mandatory)
#

# AWS credentials file
variable "aws_creds" {
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
  default     = " ricardo-terraform"
}

variable "aws_region" {
  description = "Key pair name in AWS"
  type        = string
  default     = "us-east-1"
}

# EC2 instance type
variable "instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "i4i.2xlarge"       # Type of the loader EC2 instance"
}

# Amazon Machine Image (AMI) ID
variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0bca3ed0b1ef2f2fa"             # Amazon Machine Image ID for the instances"
}


# Amazon Machine Image (AMI) Username
variable "instance_username" {
  description = "username for the AMI"
  type        = string
  default     = "ubuntu"              # Default username for the instance"
}


# Monitoring instance type
variable "monitoring_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = " m5.2xlarge"   # Type for the monitoring EC2 instance"
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
  default     = "128"                       # Number of threads for the benchmarking tool"
}

# Total number of operations to run
variable "num_of_ops" {
  description = "Total number of operations to run"
  type        = string
  default     = "46B"                        # Total number of operations to perform"
}

# Throttling for the Cassandra stress tool
variable "throttle" {
  description = "Throttling for the Cassandra stress tool (in ops/sec)"
  type        = string
  default     = "100000/s"                     # Throttling for operations per second"
}

# Environment name
variable "custom_name" {
  description = "Name for the ScyllaDB Cloud environment"
  type        = string
  default     = "Ricardo-Benchmark"         # Custom name for the benchmarking setup"
}


# Number of ScyllaDB  instances to create
variable "scylla_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "3"                   # Number of ScyllaDB nodes to deploy"
}

# Number of Loaders instances to create
variable "loader_node_count" {
  description = "Number of ScyllaDB instances to create"
  type        = string
  default     = "3"                   # Number of loaders nodes to deploy"
}

locals {
  scylla_ips  = (join(",", [for s in scylladbcloud_cluster.scylladbcloud.node_private_ips : format("%s", s)]))
  scylla_pass = data.scylladbcloud_cql_auth.scylla.password
}
