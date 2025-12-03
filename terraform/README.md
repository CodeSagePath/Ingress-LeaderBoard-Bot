# Terraform Infrastructure for Ingress Prime Leaderboard Bot

This directory contains Terraform configurations for deploying the complete infrastructure for the Ingress Prime Leaderboard Bot on AWS.

## Overview

The infrastructure includes:

- **Amazon EKS** - Kubernetes cluster for container orchestration
- **Amazon RDS** - PostgreSQL database for data storage
- **Amazon VPC** - Networking infrastructure
- **Security Groups** - Network security configuration
- **IAM Roles** - AWS Identity and Access Management
- **Monitoring** - CloudWatch and logging integration

## Prerequisites

1. **Terraform** >= 1.5.0
2. **AWS CLI** configured with appropriate permissions
3. **kubectl** for Kubernetes cluster management
4. **Helm** (optional, for additional charts)

## Setup

### 1. Configure Terraform Backend

Create an S3 bucket and DynamoDB table for Terraform state:

```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket your-terraform-state-bucket \
  --region us-west-2

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2
```

### 2. Configure Terraform Variables

Create a `terraform.tfvars` file:

```hcl
# terraform.tfvars
project_name           = "ingress-leaderboard"
environment            = "production"
aws_region             = "us-west-2"
terraform_state_bucket = "your-terraform-state-bucket"

# Kubernetes settings
kubernetes_version     = "1.28"
eks_node_instance_type = "t3.medium"
eks_node_count         = 3
eks_node_max_count     = 10
eks_node_min_count     = 3

# Database settings
db_instance_class       = "db.t3.micro"
db_allocated_storage    = 20
db_max_allocated_storage = 100

# Network settings
vpc_cidr          = "10.0.0.0/16"
private_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets    = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# Domain settings
domain_name      = "your-domain.com"
certificate_arn  = "arn:aws:acm:us-west-2:123456789012:certificate/your-cert-id"
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan and Apply

```bash
# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

## Modules Used

- **terraform-aws-modules/vpc/aws** - VPC networking
- **terraform-aws-modules/eks/aws** - EKS Kubernetes cluster

## File Structure

```
terraform/
├── main.tf              # Main Terraform configuration
├── variables.tf         # Variable definitions
├── outputs.tf           # Output definitions
├── eks.tf              # EKS cluster configuration
├── networking.tf       # VPC and networking
├── rds.tf              # RDS database configuration
└── README.md           # This file
```

## Security Considerations

### Network Security

- Private subnets for database and application instances
- Security groups restrict traffic to necessary ports
- NAT gateways for outbound internet access
- No direct database access from the internet

### Database Security

- Encryption at rest and in transit
- Automated backups with retention policies
- Enhanced monitoring in production
- Passwords stored in AWS Secrets Manager

### Access Control

- IAM roles with least privilege principle
- OIDC provider for Kubernetes service accounts
- Separate roles for different components

## Monitoring and Logging

### CloudWatch Integration

- Container insights for EKS
- RDS enhanced monitoring
- VPC flow logs
- CloudTrail for API auditing

### Kubernetes Monitoring

- Metrics collection enabled
- Health check endpoints
- Resource usage monitoring

## Backup and Disaster Recovery

### Database Backups

- Automated daily backups
- Point-in-time recovery
- Cross-region backup replication (configurable)

### Infrastructure

- Infrastructure as Code for reproducibility
- State locking and versioning
- Multiple environment support

## Environment Management

### Production Environment

```bash
terraform apply -var-file="production.tfvars"
```

### Staging Environment

```bash
terraform apply -var-file="staging.tfvars"
```

### Development Environment

```bash
terraform apply -var-file="development.tfvars"
```

## Cost Optimization

### Compute Resources

- Auto Scaling Group for EKS nodes
- Spot instances for non-critical workloads
- Right-sizing based on usage metrics

### Storage

- EBS gp3 volumes for better performance
- Lifecycle policies for data retention
- Compression and deduplication

### Network

- Data Transfer optimization
- Regional deployment for latency reduction
- VPC endpoints for AWS services

## Troubleshooting

### Common Issues

1. **Terraform State Lock Issues**
   ```bash
   terraform force-unlock LOCK_ID
   ```

2. **EKS Cluster Connection Issues**
   ```bash
   aws eks update-kubeconfig --name <cluster-name>
   kubectl get nodes
   ```

3. **Database Connection Issues**
   - Check security group rules
   - Verify subnet group configuration
   - Check VPC routing

### Useful Commands

```bash
# Check Terraform state
terraform show

# Import existing resources
terraform import aws_vpc.main vpc-id

# Destroy infrastructure
terraform destroy

# Get output values
terraform output cluster_name
terraform output configure_kubectl
```

## Maintenance

### Regular Tasks

1. **Update Terraform modules**
   ```bash
   terraform init -upgrade
   ```

2. **Review and update IAM policies**
3. **Monitor resource usage and costs**
4. **Update Kubernetes versions**

### Backup Strategy

- Terraform state is stored in S3 with versioning
- Database backups are automated
- Infrastructure is reproducible from code

## Compliance

This infrastructure follows AWS best practices for:

- **Security** - encryption, access control, network segmentation
- **Reliability** - high availability, backup, monitoring
- **Performance** - auto scaling, optimized resource allocation
- **Cost Optimization** - right-sizing, reserved instances

## Support

For issues with this infrastructure:

1. Check AWS CloudWatch logs
2. Review Terraform state and configuration
3. Consult AWS documentation
4. Review Kubernetes cluster events
5. Check network connectivity