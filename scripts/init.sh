#!/usr/bin/env bash

set -xe

# log all user data invocations to console:
# from https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-log-user-data/
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# TODO: see if this is necessary?
# disables automatic updates
systemctl disable --now apt-daily{,-upgrade}.{timer,service}

# wait for any unattended upgrades to finish
echo "Waiting for unattended upgrades to finish..."
systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true

echo "Updating..."
apt-get update

echo "Installing pip..."
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
~/.local/bin/pip install awscli --upgrade --user

echo "Logging in to ECS registry..."
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}
export AWS_DEFAULT_REGION=${AWS_REGION}
$(~/.local/bin/aws ecr get-login --no-include-email)
echo "Logged in!"

if [ ${GPU_HOST} -eq 0 ]; then
    # Extract number of GPUs on instance
    echo "Getting number of GPUs..."
    apt-get install jq

    # get xml2json repo from git
    sudo git clone https://github.com/Cheedoong/xml2json.git /opt/x2j
    cd /opt/x2j; sudo make; cd -
    export NUM_GPUS=$(nvidia-smi -x -q | /opt/x2j/xml2json | jq .nvidia_smi_log.attached_gpus)
fi

echo "Setting permissions on docker..."
sudo chown ubuntu:ubuntu /home/ubuntu/.docker -R

echo "Running initialization script..."
python3 /opt/init/start.py \
    --aws-access-key ${AWS_ACCESS_KEY} \
    --aws-secret-key ${AWS_SECRET_KEY} \
    --aws-default-region ${AWS_REGION} \
    --gpu ${GPU_HOST} \
    $([ ${GPU_HOST} -eq 0 ] && echo "" || echo "--num-gpus $${NUM_GPUS}") \
    --role ${ROLE}