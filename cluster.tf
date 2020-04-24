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

    # HTTP access (for Git)
    egress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # HTTPS access (for Git)
    egress {
        from_port = 443
        to_port = 443
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # master <-> worker
    ingress {
        from_port = var.worker_port
        to_port = var.master_port
        protocol = "tcp"
    }
}

resource "aws_security_group" "ec2-worker" {
    name = "ec2-cluster-node"
    description = "Cluster worker communication with master node"
    vpc_id = aws_vpc.main.id

    # HTTP access (for Git)
    egress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # HTTPS access (for Git)
    egress {
        from_port = 443
        to_port = 443
        protocol = "tcp"
        cidr_blocks = [ "0.0.0.0/0" ]
    }

    # master <-> worker
    ingress {
        from_port = var.master_port
        to_port = var.worker_port
        protocol = "tcp"
    }

    # worker <-> worker
    egress {
        from_port = var.worker_port
        to_port = var.worker_port
        protocol = "tcp"
    }

    ingress {
        from_port = var.worker_port
        to_port = var.worker_port
        protocol = "tcp"
    }
}