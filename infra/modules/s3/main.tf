# =============================================================
# S3 Module — Data Lake Buckets
# Creates Bronze, Silver, Gold, Logs, and Terraform state buckets
# =============================================================

variable "project_name" {
  description = "Project name prefix for bucket naming"
  type        = string
  default     = "f1-de"
}

variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
  default     = "dev"
}

# ── Bronze Bucket — Raw Zone ─────────────────────────────────
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze-${var.environment}"

  tags = {
    Name        = "F1 Bronze Layer"
    Environment = var.environment
    Layer       = "bronze"
  }
}

resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Silver Bucket — Cleaned Zone ─────────────────────────────
resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-silver-${var.environment}"

  tags = {
    Name        = "F1 Silver Layer"
    Environment = var.environment
    Layer       = "silver"
  }
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Gold Bucket — Business Zone ──────────────────────────────
resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold-${var.environment}"

  tags = {
    Name        = "F1 Gold Layer"
    Environment = var.environment
    Layer       = "gold"
  }
}

resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Logs Bucket — Airflow / Application Logs ────────────────
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}"

  tags = {
    Name        = "F1 Logs"
    Environment = var.environment
    Layer       = "logs"
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: move logs to cheaper storage after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "archive-old-logs"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 90
    }
  }
}

# ── Outputs ───────────────────────────────────────────────────
output "bronze_bucket_name" {
  value = aws_s3_bucket.bronze.id
}

output "silver_bucket_name" {
  value = aws_s3_bucket.silver.id
}

output "gold_bucket_name" {
  value = aws_s3_bucket.gold.id
}

output "logs_bucket_name" {
  value = aws_s3_bucket.logs.id
}

output "bronze_bucket_arn" {
  value = aws_s3_bucket.bronze.arn
}

output "silver_bucket_arn" {
  value = aws_s3_bucket.silver.arn
}

output "gold_bucket_arn" {
  value = aws_s3_bucket.gold.arn
}

output "logs_bucket_arn" {
  value = aws_s3_bucket.logs.arn
}
