# =============================================================
# F1 Data Engineering — AWS Infrastructure (Dev Environment)
# =============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "f1-de"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# ── S3 Data Lake ────────────────────────────────────────────
module "s3" {
  source       = "../../modules/s3"
  project_name = var.project_name
  environment  = var.environment
}

# ── Outputs ─────────────────────────────────────────────────
output "bronze_bucket" {
  value = module.s3.bronze_bucket_name
}

output "silver_bucket" {
  value = module.s3.silver_bucket_name
}

output "gold_bucket" {
  value = module.s3.gold_bucket_name
}

output "logs_bucket" {
  value = module.s3.logs_bucket_name
}
