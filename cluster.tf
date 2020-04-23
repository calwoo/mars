###################################
# Cluster distributed state backend

terraform {
    backend "s3" {
        region = "us-east-1"
        bucket = "cwoo-generic"
        key    = "terraform.tfstate"
    }
}

###################
# Cluster instances

