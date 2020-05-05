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

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.key_file)
    host        = self.public_ip
  }

  # Provisioning: first, grab IPs from node creation...
  provisioner "local-exec" {
    command = <<EOT
      if [ ! -d artifacts ]; then mkdir artifacts; fi
      echo ${self.public_ip} > artifacts/master_public.txt
      echo ${self.private_ip} > artifacts/master_private.txt
      > artifacts/worker_public.txt
      > artifacts/worker_private.txt
    EOT
  }

  # ...then push config files to instance...
  provisioner "remote-exec" {
    inline = [
      "mkdir /tmp/config/",
      "mkdir /tmp/init/"
    ]
  }

  provisioner "file" {
    source      = "config/${var.cluster_type}/"
    destination = "/tmp/config"
  }

  # ...and initialization scripts...
  provisioner "file" {
    source      = "scripts/master/"
    destination = "/tmp/init"
  }

  provisioner "file" {
    content     = data.template_file.master_init.rendered
    destination = "/tmp/init/init.sh"
  }

  # ...finally, run initialization.
  provisioner "remote-exec" {
    inline = [
      "sudo chmod +x /tmp/init/init.sh",
      "sudo cp -r /tmp/config /opt/config",
      "sudo cp -r /tmp/init /opt/init",
      "sudo /opt/init/init.sh"
    ]
  }

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

  user_data = base64encode(data.template_file.worker_init.rendered)

  tags = {
    name        = "ec2-worker-tpl"
    description = "Launch template for EC2 worker nodes"
  }
}

resource "aws_autoscaling_group" "ec2-cluster-asg" {
  min_size         = 1
  max_size         = var.max_workers
  desired_capacity = var.n_workers

  vpc_zone_identifier = [aws_subnet.main_subnet.id]

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity  = 1
      spot_allocation_strategy = "lowest-price"
      spot_max_price           = var.spot_price
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.ec2-worker.id
        version            = aws_launch_template.ec2-worker.latest_version
      }
    }
  }

  depends_on = [aws_spot_instance_request.ec2-master]

  provisioner "local-exec" {
    command = <<EOT
      echo ${self.id} > artifacts/asg_id.txt
      aws s3 cp config/${var.cluster_type}/ s3://${var.config_s3_bucket}/mars/${aws_spot_instance_request.ec2-master.id}/config --recursive
      aws s3 cp scripts/worker/ s3://${var.config_s3_bucket}/mars/${aws_spot_instance_request.ec2-master.id}/init --recursive
      aws s3 cp artifacts/ s3://${var.config_s3_bucket}/mars/${aws_spot_instance_request.ec2-master.id}/artifacts --recursive
    EOT
  }

  tags = [
    {
      key                 = "name"
      value               = "ec2-worker"
      propagate_at_launch = true
    },
    {
      key                 = "description"
      value               = "A single node on the EC2 cluster"
      propagate_at_launch = true
    }
  ]
}

data "aws_instances" "cluster" {
  filter {
    name   = "instance.group-id"
    values = [aws_security_group.ec2-cluster-sg.id]
  }

  filter {
    name   = "tag:name"
    values = ["ec2-worker"]
  }

  depends_on = [
    aws_autoscaling_group.ec2-cluster-asg,
    aws_spot_instance_request.ec2-master
  ]
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

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access (for Git)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.main_subnet.cidr_block]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow internal node communication
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
