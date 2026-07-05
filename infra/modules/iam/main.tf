# =============================================================
# IAM Module — Roles and Policies
# Creates least-privilege roles for Glue, EMR, and Redshift
# to access the F1 Data Lake S3 buckets.
# =============================================================

variable "project_name" {
  type    = string
  default = "f1-de"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "bronze_bucket_arn" {
  type = string
}

variable "silver_bucket_arn" {
  type = string
}

variable "gold_bucket_arn" {
  type = string
}

variable "logs_bucket_arn" {
  type = string
}

# ── Glue Service Role ──────────────────────────────────────
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "F1 Glue Role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_policy" "glue_s3_access" {
  name        = "${var.project_name}-glue-s3-access-${var.environment}"
  description = "Allows Glue to read/write Bronze, Silver, Gold buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.bronze_bucket_arn,
          "${var.bronze_bucket_arn}/*",
          var.silver_bucket_arn,
          "${var.silver_bucket_arn}/*",
          var.gold_bucket_arn,
          "${var.gold_bucket_arn}/*",
          var.logs_bucket_arn,
          "${var.logs_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_s3_access" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_s3_access.arn
}

# ── EMR Service Role ────────────────────────────────────────
resource "aws_iam_role" "emr_service_role" {
  name = "${var.project_name}-emr-service-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "elasticmapreduce.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "F1 EMR Service Role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "emr_service_role" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

resource "aws_iam_role" "emr_ec2_role" {
  name = "${var.project_name}-emr-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "F1 EMR EC2 Role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "emr_ec2_role" {
  role       = aws_iam_role.emr_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

resource "aws_iam_instance_profile" "emr_ec2_profile" {
  name = "${var.project_name}-emr-ec2-profile-${var.environment}"
  role = aws_iam_role.emr_ec2_role.name
}

# ── Redshift Service Role (for COPY from S3) ────────────────
resource "aws_iam_role" "redshift_role" {
  name = "${var.project_name}-redshift-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "redshift.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "F1 Redshift Role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "redshift_s3_read" {
  name        = "${var.project_name}-redshift-s3-read-${var.environment}"
  description = "Allows Redshift to read from Gold bucket via COPY command"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.gold_bucket_arn,
          "${var.gold_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "redshift_s3_read" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = aws_iam_policy.redshift_s3_read.arn
}

# ── Outputs ───────────────────────────────────────────────────
output "glue_role_arn" {
  value = aws_iam_role.glue_role.arn
}

output "emr_service_role_arn" {
  value = aws_iam_role.emr_service_role.arn
}

output "emr_ec2_instance_profile_name" {
  value = aws_iam_instance_profile.emr_ec2_profile.name
}

output "redshift_role_arn" {
  value = aws_iam_role.redshift_role.arn
}
