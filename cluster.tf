###################################
# Cluster distributed state backend

terraform {
    backend "s3" {
        bucket = var.s3_state_bucket
        key    = var.s3_state_key
        region = var.aws_region
    }
}

###################
# Cluster instances

