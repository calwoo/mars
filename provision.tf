data "template_file" "master" {
    template = file("scripts/master.sh")
    vars = {
        AWS_CREDENTIALS = var.credentials
    }
}

data "template_file" "worker" {
    template = file("scripts/worker.sh")
    vars = {
        AWS_CREDENTIALS = var.credentials
    }
}