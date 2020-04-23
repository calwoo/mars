provider "aws" {
    region  = "${var.aws_region}"
    version = "~> 2.0"
    shared_credentials_file = "${var.credentials}"
    profile                 = "${var.profile}"
}