data "template_file" "master" {
  template = file("${path.module}/scripts/master.sh")
  vars = {
    AWS_ACCESS_KEY = var.aws_access_key
    AWS_SECRET_KEY = var.aws_secret_key
    AWS_REGION     = var.aws_region
    NODE_IMAGE     = var.master_image
    GPU_HOST       = contains(["p", "g"], lower(substr(var.instance_type, 0, 1))) ? 1 : 0
    MASTER_PORT    = var.master_port
    WORKER_PORT    = var.worker_port
    NUM_NODES      = var.n_workers + 1
  }
}

data "template_file" "worker" {
  template = file("${path.module}/scripts/worker.sh")
  vars = {
    AWS_ACCESS_KEY = var.aws_access_key
    AWS_SECRET_KEY = var.aws_secret_key
    AWS_REGION     = var.aws_region
    NODE_IMAGE     = var.worker_image
    GPU_HOST       = contains(["p", "g"], lower(substr(var.instance_type, 0, 1))) ? 1 : 0
    MASTER_PORT    = var.master_port
    MASTER_ADDR    = aws_spot_instance_request.ec2-master.private_ip
  }
}

data "template_file" "init" {
  template = file("${path.module}/scripts/init.sh")
  vars = {
    AWS_ACCESS_KEY = var.aws_access_key
    AWS_SECRET_KEY = var.aws_secret_key
    AWS_REGION     = var.aws_region
    GPU_HOST       = contains(["p", "g"], lower(substr(var.instance_type, 0, 1))) ? 1 : 0
  }
}
