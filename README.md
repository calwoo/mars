## mars

EC2 clusters for distributed deep learning launched by Terraform. Named after the book series by Kim Stanley Robinson on the terraforming of the planet Mars.

### initialization

To initialize a cluster, you can use the `run.sh` script as an entrypoint, or you can manually initialize using the commands

```
terraform init
terraform apply
```

### configuration

The Mars cluster requires a number of configuration files to properly initialize. All AWS specific configs (such as login credentials and cluster architecture) should be defined in a Terraform variable file `terraform.tfvars`. The remaining configuration involves dealing with what happens after AWS constructs the instances.

