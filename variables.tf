variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region where cluster is to be constructed"
}

variable "credentials" {
  type        = string
  default     = "~/.aws/credentials"
  description = "AWS access keys to use to login"
}

variable "aws_access_key" {
  type        = string
  description = "AWS access key"
}

variable "aws_secret_key" {
  type        = string
  description = "AWS secret access key"
}

variable "profile" {
  type        = string
  default     = "default"
  description = "AWS profile to use to login"
}

###################
# Cluster variables

variable "master_image" {
  type        = string
  description = "Docker image to be used on cluster master node"
}

variable "worker_image" {
  type        = string
  description = "Docker image to be used on cluster worker node"
}

variable "master_port" {
  type        = number
  default     = 1234
  description = "Port of master node for distributed handshake"
}

variable "master_ip_addr" {
  type        = string
  default     = "127.0.0.1"
  description = "IP address of master node for distributed handshake"
}

variable "worker_port" {
  type        = number
  default     = 1235
  description = "Port of worker nodes for distributed handshake"
}

variable "my_ip" {
  type        = string
  description = "Your IP address"
}

####################
# Instance variables

variable "instance_ami" {
  type        = string
  default     = "ami-0f6127e61a87f8677"
  description = "Default AMI for EC2 nodes"
}

variable "spot_price" {
  type        = number
  default     = 0.5
  description = "Maximum spot price for EC2 request"
}

variable "instance_type" {
  type        = string
  default     = "t2.micro"
  description = "Instance type of the cluster nodes"
}

variable "key_name" {
  type        = string
  description = "Key to use to access AWS EC2 instances"
}

variable "max_workers" {
  type        = number
  default     = 3
  description = "Max number of worker nodes to launch"
}

variable "n_workers" {
  type        = number
  default     = 1
  description = "Number of worker nodes to launch"
}
