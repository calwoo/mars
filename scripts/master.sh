#!/usr/bin/env bash

set -xe

# log all user data invocations to console:
# from https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-log-user-data/
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Updating..."
apt-get update

echo "Installing pip..."
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py --user
~/.local/bin/pip install awscli --upgrade --user

echo "Logging in to ECS registry..."
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}
export AWS_DEFAULT_REGION=${AWS_REGION}
$(~/.local/bin/aws ecr get-login --no-include-email)
echo "Logged in!"

echo "Loading docker image..."
if [ ${GPU_HOST} -eq 0 ]; then
    docker run -i -t -d \
        --network host \
        -e MASTER_PORT=${MASTER_PORT} \
        -e WORKER_PORT=${WORKER_PORT} \
        -e NUM_NODES=${NUM_NODES} \
        ${CLUSTER_IMAGE}
else
    docker run -it \
        --network host \
        --gpus all \
        -e MASTER_PORT=${MASTER_PORT} \
        -e WORKER_PORT=${WORKER_PORT} \
        -e NUM_NODES=${NUM_NODES} \
        ${CLUSTER_IMAGE}
fi