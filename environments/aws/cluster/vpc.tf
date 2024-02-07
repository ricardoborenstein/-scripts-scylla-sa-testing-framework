# Virtual Private Cloud (VPC) IP range
variable "custom_vpc" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/24"
}

# EC2 instance tenancy
variable "instance_tenancy" {
  description = "EC2 instance tenancy, default or dedicated"
  type        = string
  default     = "default"
}


# Create Virtual Private Cloud
resource "aws_vpc" "custom_vpc" {
  cidr_block           = var.custom_vpc
  instance_tenancy     = var.instance_tenancy
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
  "Name" = "${var.custom_name}-VPC"
  "Project"   = "${var.custom_name}"
  "Type" =  "VPC"
}
}

# Create Public subnet
resource "aws_subnet" "public_subnet" {
  count                   = 1 # Always create one subnet
  vpc_id                  = aws_vpc.custom_vpc.id
  availability_zone       = data.aws_availability_zones.azs.names[0] # First AZ
  cidr_block              = cidrsubnet(var.custom_vpc, 4, 0) # Adjusted for a single subnet
  map_public_ip_on_launch = true
  tags = {
    "Name" = "${var.custom_name}-Public-Subnet-${count.index}"
    "Project" = var.custom_name
  }
}


# Create Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.custom_vpc.id

  tags = {
    "Name" = "${var.custom_name}-Internet-Gateway"
    "Project"   = "${var.custom_name}"
  }
}

# Create Public Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.custom_vpc.id

  tags = {
    "Name" = "${var.custom_name}-Public-RouteTable"
    "Project"   = "${var.custom_name}"
  }
}

# Create Public Route
resource "aws_route" "public_route" {
  route_table_id         = aws_route_table.public_rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id

}

# Create Public Route Table Association
resource "aws_route_table_association" "public_rt_association" {
  route_table_id = aws_route_table.public_rt.id
  subnet_id      = aws_subnet.public_subnet[0].id
}

# # Accepter's side of the connection
# resource "aws_vpc_peering_connection_accepter" "current" {
#   vpc_peering_connection_id = scylladbcloud_vpc_peering.scylladbcloud.connection_id
#   auto_accept               = true

#   tags = {
#     Side = "Accepter"
#   }
# }

# # Create SC Route:
# resource "aws_route" "scylla-cloud" {
#   route_table_id            = aws_route_table.public_rt.id
#   destination_cidr_block    = "172.31.0.0/16"
#   vpc_peering_connection_id = scylladbcloud_vpc_peering.scylladbcloud.connection_id
#   #  depends_on                = [aws_route_table.testing]
# }