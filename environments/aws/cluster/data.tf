data "aws_availability_zones" "azs" {}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_instances" "scylladb" {
  filter {
    name   = "tag:Project"
    values = [var.custom_name]
  }

  filter {
    name   = "tag:Type"
    values = ["Scylla"]
  }
}
data "aws_vpc" "selected" {
    id = aws_vpc.custom_vpc.id
}

# data "aws_security_group" "sg" {
#   name = "${var.custom_name}-sg"
#   vpc_id      = aws_vpc.custom_vpc.id
#   # ... other configuration ...
# }

# data "aws_subnets" "public_subnets" {
#       filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.selected.id]
#   }
  # You can also include filters here if you're looking for subnets that match specific criteria
# }

# data "aws_subnet" "public_subnets" {
#   for_each = toset(data.aws_subnets.public_subnets.ids)
#   id       = each.value
# }




# Output to display private IPs of matched instances
output "scylladb_private_ips" {
  value = data.aws_instances.scylladb.private_ips
}

