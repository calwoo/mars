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
    cidr_block = "10.0.0.0/16"
    instance_tenancy = "default"
    enable_dns_hostnames = true
    enable_dns_support = true
}





#########################
# Cluster security groups

resource "aws_security_group" "ec2-master" {
    name = "ec2-cluster-master"
    description = "Cluster master communication with worker nodes"
    vpc_id = aws_vpc.main.id

    # SSH access
    ingress {
        from_port = 22
        to_port   = 22
        protocol = "tcp"
        cidr_blocks = [ "${var.my_ip}/32" ]
    }

    # Jupyter notebook access
    ingress {
      from_port = 8888
      to_port = 8888
      protocol = "tcp"
      cidr_blocks = [ "${var.my_ip}/32" ]
    }

    # Git access
    ingress {
      from_port = 0
      to_port = 0
      protocol = "-1"
      cidr_blocks = [ "${var.my_ip}/32" ]
    }
}