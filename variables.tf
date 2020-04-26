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

variable "profile" {
  type        = string
  default     = "default"
  description = "AWS profile to use to login"
}

###################
# Cluster variables

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
  default     = "ami-085925f297f89fce1"
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
