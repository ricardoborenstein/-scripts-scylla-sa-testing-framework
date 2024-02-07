#
# Set the following variables (mandatory)
#
variable "custom_name" {
  description = "Name to be used as TAG"
  type        = string
  default     = "ricardo-testing"
}
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
  default     = "ricardo-terraform"
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
  default     = "i4i.xlarge"
}
# ScyllaDB instance type
variable "scylla_num_nodes" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "3"
}
# Amazon Machine Image (AMI) ID
variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0c7217cdde317cfec"
}


# Monitoring instance type
variable "monitoring_instance_type" {
  description = "Type of the EC2 instance"
  type        = string
  default     = "m5.2xlarge"
}


