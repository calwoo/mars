output "worker_instance_ips" {
    value = data.aws_instances.cluster.public_ips
}

output "master-ssh" {
    value = "ssh -i \"~/.ssh/${var.key_name}\" -L 8000:localhost:8888 ec2-user@${aws_spot_instance_request.ec2-master.public_ip}"
}