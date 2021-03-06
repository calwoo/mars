data "template_file" "master_init" {
  template = file("${path.module}/scripts/master/init.sh")
  vars = {
    AWS_ACCESS_KEY = var.aws_access_key
    AWS_SECRET_KEY = var.aws_secret_key
    AWS_REGION     = var.aws_region
    GPU_HOST       = contains(["p", "g"], lower(substr(var.instance_type, 0, 1))) ? 1 : 0
    NB_PASS        = random_password.nb_password.result
    ROLE           = "master"
  }
}

data "template_file" "worker_init" {
  template = file("${path.module}/scripts/worker/init.sh")
  vars = {
    AWS_ACCESS_KEY   = var.aws_access_key
    AWS_SECRET_KEY   = var.aws_secret_key
    AWS_REGION       = var.aws_region
    CONFIG_S3_BUCKET = var.config_s3_bucket
    MASTER_NODE_ID   = aws_spot_instance_request.ec2-master.id
    GPU_HOST         = contains(["p", "g"], lower(substr(var.instance_type, 0, 1))) ? 1 : 0
    NB_PASS          = random_password.nb_password.result
    ROLE             = "worker"
  }
}

resource "random_password" "nb_password" {
  length           = 16
  special          = true
  override_special = "_%@"
}
