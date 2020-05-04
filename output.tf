output "master_public_ip" {
    value = aws_spot_instance_request.ec2-master.public_ip
}

output "master_private_ip" {
    value = aws_spot_instance_request.ec2-master.private_ip
}

output "worker_instance_public_ips" {
    value = data.aws_instances.cluster.public_ips
}

output "worker_instance_private_ips" {
    value = data.aws_instances.cluster.private_ips
}

output "master-ssh" {
    value = "ssh -i \"~/.ssh/${var.key_name}.pem\" ubuntu@${aws_spot_instance_request.ec2-master.public_ip}"
}

output "notebook-login" {
    value = random_password.nb_password.result
}