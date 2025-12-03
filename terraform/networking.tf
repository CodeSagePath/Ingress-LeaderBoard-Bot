# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.5"

  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

  azs             = data.aws_availability_zones.available.names
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Database subnet group
  create_database_subnet_group           = true
  create_database_subnet_route_table     = true
  database_subnets                        = var.private_subnets

  # Tags
  tags = local.tags

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
}

# EIPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = length(data.aws_availability_zones.available.names)
  domain = "vpc"

  tags = merge(local.tags, {
    Name = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
  })

  depends_on = [module.vpc]
}