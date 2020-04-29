#!/usr/bin/env bash

### Run script for an EC2 cluster (possible GPU-enabled). 

if ! [ -x "$(command -v terraform)" ]; then
    # Installs terraform if it doesn't exist
    if [[ "$OSTYPE" == "linux-gnu" ]]; then
        echo "Linux detected... installing terraform"
        wget -v -O /tmp/tf.zip \
            https://releases.hashicorp.com/terraform/0.12.24/terraform_0.12.24_linux_amd64.zip
        unzip /tmp/tf.zip -d /tmp/
        mkdir ~/.terraform
        mv /tmp/terraform ~/.terraform/terraform
        echo "export PATH=\$PATH:~/terraform" >> ~/.bashrc
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Mac OSX detected... installing terraform"
        echo "NB: If this fails, install homebrew!"
        brew install terraform
    fi

    # Verify terraform install
    terraform version
fi

echo "Initializing EC2 cluster..."
terraform init
terraform apply -auto-approve

if ! [ -d "./artifacts/" ]; then
    echo "Created directory for terraform artifacts"
    mkdir ./artifacts/
fi

# Create terraform artifacts
echo "Creating terraform artifacts..."
terraform output -json | jq .master_public_ip.value > ./artifacts/master_public.txt
terraform output -json | jq .master_private_ip.value > ./artifacts/master_private.txt
terraform output -json | jq .worker_instance_public_ips.value[] > ./artifacts/worker_public.txt