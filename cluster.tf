###################################
# Cluster distributed state backend

terraform {
  backend "s3" {
    region = "us-east-1"
    bucket = "cwoo-generic"
    key    = "terraform.tfstate"
  }
}

#################
# Cluster network

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    description = "VPC for cluster"
  }
}

resource "aws_subnet" "main_subnet" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.0.0/16"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "main_igw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_default_route_table" "main_route_table" {
  default_route_table_id = aws_vpc.main.default_route_table_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main_igw.id
  }
}

###################
# Cluster instances

resource "aws_spot_instance_request" "ec2-master" {
  ami                         = var.instance_ami
  instance_type               = var.instance_type
  spot_price                  = var.spot_price
  wait_for_fulfillment        = true
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.ec2-cluster-sg.id]
  subnet_id                   = aws_subnet.main_subnet.id
  associate_public_ip_address = true

  tags = {
    name        = "ec2-master"
    description = "Master node of cluster"
  }
}

resource "aws_launch_template" "ec2-worker" {
  instance_type = var.instance_type
  image_id      = var.instance_ami
  key_name      = var.key_name

  monitoring {
    enabled = true
  }

  network_interfaces {
    associate_public_ip_address = true
    delete_on_termination       = true
    security_groups             = [aws_security_group.ec2-cluster-sg.id]
    subnet_id                   = aws_subnet.main_subnet.id
  }

  tags = {
    name        = "ec2-worker-tpl"
    description = "Launch template for EC2 worker nodes"
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

  # HTTP access (for Git)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.main_subnet.cidr_block]
  }

  # HTTPS access (for Git)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.main_subnet.cidr_block]
  }
}
