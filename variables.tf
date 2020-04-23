variable "aws_region" {
    type = "string"
    default = "us-east-1"
    description = "AWS region where cluster is to be constructed"
}

variable "credentials" {
    type = "string"
    default = "~/.aws/credentials"
    description = "AWS access keys to use to login"
}

variable "profile" {
    type = "string"
    default = "default"
    description = "AWS profile to use to login"
}