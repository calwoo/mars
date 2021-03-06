#!/usr/bin/env bash

### Set working directory of script to path where file exists
scriptdir="$(dirname "$0")"
cd "$scriptdir"

figlet mars cluster

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

cd ..

echo "Initializing EC2 cluster..."
terraform init > /dev/null
terraform apply -auto-approve \
    -var="key_file=$1" \
    -var="n_workers=$2" \
    -var="instance_type=$3"

if ! [ -d "./artifacts/" ]; then
    echo "Created directory for terraform artifacts"
    mkdir ./artifacts/
fi

# Create terraform artifacts
echo "Creating terraform artifacts..."
echo "[master]" > ./ansible/inventory
terraform output -json | jq -r '.master_public_ip.value + " ansible_user=ubuntu"' >> ./ansible/inventory
echo -e "\n[workers]" >> ./ansible/inventory
terraform output -json | jq -r '.worker_instance_public_ips.value[] + " ansible_user=ubuntu"' >> ./ansible/inventory

echo -e "\n" >> ./ansible/inventory
cat <<EOT >> ./ansible/inventory
[mars:children]
master
workers

[mars:vars]
ansible_ssh_user=ubuntu
ansible_ssh_private_key_file=$1
EOT

echo -e "Giving instances time to warm up...\n"
sleep 10

figlet provisioning...

export ANSIBLE_CONFIG=./ansible/ansible.cfg

ansible-playbook ./ansible/playbook.yml \
    --private-key $1 \
    --inventory-file ./ansible/inventory \
    --forks 1 \
    --user ubuntu \
    --timeout 300

figlet ready!

echo -e "\n"
terraform output