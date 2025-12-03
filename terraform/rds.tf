# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = module.vpc.database_subnets

  tags = merge(local.tags, {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  })
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = module.vpc.vpc_id

  # Allow traffic from EKS nodes
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  })
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  # Engine settings
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  # Database settings
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  # Storage settings
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true

  # Network settings
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Backup settings
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring
  monitoring_interval = var.environment == "production" ? 60 : 0
  monitoring_role_arn = var.environment == "production" ? aws_iam_role.rds_enhanced_monitoring.arn : null

  # Performance Insights
  performance_insights_enabled          = var.environment == "production"
  performance_insights_retention_period = var.environment == "production" ? 7 : 0

  # Deletion protection
  deletion_protection = var.environment == "production"

  # Skip final snapshot for non-production
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-${var.environment}-final-snapshot" : null

  tags = merge(local.tags, {
    Name = "${var.project_name}-${var.environment}-db"
  })
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Enhanced monitoring IAM role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.environment == "production" ? 1 : 0

  name = "${var.project_name}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count      = var.environment == "production" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = aws_iam_role.rds_enhanced_monitoring[0].name
}

# Store database password in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project_name}/${var.environment}/database/password"
  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    password = random_password.db_password.result
  })
}