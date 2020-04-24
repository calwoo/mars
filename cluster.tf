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

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    description = "VPC for cluster"
  }
}







#########################
# Cluster security groups

resource "aws_security_group" "ec2-cluster-sg" {
  name        = "ec2-cluster"
  description = "Cluster security group with basic permissions"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.my_ip}/32"]
  }
}
