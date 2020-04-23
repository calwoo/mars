variable "aws_region" {
    type = string
    default = "us-east-1"
    description = "AWS region where cluster is to be constructed"
}

variable "credentials" {
    type = string
    default = "~/.aws/credentials"
    description = "AWS access keys to use to login"
}

variable "profile" {
    type = string
    default = "default"
    description = "AWS profile to use to login"
}

variable "s3_state_bucket" {
    description = "S3 bucket to store Terraform state"
}

variable "s3_state_key" {
    default = "terraform.tfstate"
    description = "Key for stored Terraform state in backend"
}