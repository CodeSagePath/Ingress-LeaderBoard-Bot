terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubectl = {
      source  = "alekc/kubectl"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend for storing Terraform state
  backend "s3" {
    bucket = var.terraform_state_bucket
    key    = "ingress-leaderboard/terraform.tfstate"
    region = var.aws_region

    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

# Configure AWS provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ingress-leaderboard"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.token
  }
}

provider "kubectl" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.token
  load_config_file       = false
}

# Data sources
data "aws_eks_cluster_auth" "token" {
  name = module.eks.cluster_name
}

data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# Random suffix for unique resource naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Local values
locals {
  cluster_name = "${var.project_name}-${var.environment}-${random_string.suffix.result}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}