# EKS Cluster Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.15"

  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  # Create AWS IAM role for service account
  iam_role_name = "${var.project_name}-${var.environment}-cluster-role"

  eks_managed_node_groups = {
    main = {
      name = "${var.project_name}-${var.environment}-nodes"

      instance_types = [var.eks_node_instance_type]

      min_size     = var.eks_node_min_count
      max_size     = var.eks_node_max_count
      desired_size = var.eks_node_count

      # Security group settings
      vpc_security_group_ids = [aws_security_group.eks_nodes.id]

      # IAM role for nodes
      iam_role_arn = aws_iam_role.eks_nodes.arn

      # Node group settings
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
      instance_types = [var.eks_node_instance_type]

      # Labels and taints
      labels = {
        role = "general"
      }

      # Update settings
      update_config = {
        max_unavailable_percentage = 33
      }

      # Tags
      tags = local.tags
    }
  }

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = local.tags
}

# EKS Node IAM Role
resource "aws_iam_role" "eks_nodes" {
  name = "${var.project_name}-${var.environment}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment"eks_container_registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.eks_nodes.name
}

# EKS Security Group
resource "aws_security_group" "eks_nodes" {
  name        = "${var.project_name}-${var.environment}-eks-nodes"
  description = "Security group for EKS nodes"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

# OIDC provider for EKS
data "tls_certificate" "eks" {
  url = module.eks.cluster_oidc_issuer_url
}

resource "aws_iam_oidc_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  provider_name   = module.eks.cluster_oidc_issuer_url
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}