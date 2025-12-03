variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ingress-leaderboard"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "eks_node_count" {
  description = "Number of EKS worker nodes"
  type        = number
  default     = 3
}

variable "eks_node_max_count" {
  description = "Maximum number of EKS worker nodes"
  type        = number
  default     = 10
}

variable "eks_node_min_count" {
  description = "Minimum number of EKS worker nodes"
  type        = number
  default     = 3
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ingress_leaderboard"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "postgres"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the domain"
  type        = string
}

variable "enable_monitoring" {
  description = "Enable monitoring and logging"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable backup services"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}