#!/usr/bin/env python3

"""
This programmatically launches a PyTorch distributed training job on a custom EC2 training
cluster.
"""

import sys
import os
import argparse
import logging

from paramiko import SSHClient, AutoAddPolicy
from paramiko.auth_handler import AuthenticationException

logger = logging.getLogger("launch")
logger.setLevel(logging.INFO)

class ClusterSSHClient:
    """
    SSH client to interact with cluster.
    """
    
    def __init__(self, host, user, ssh_key_path):
        self.host = host
        self.user = user
        self.ssh_key_path = ssh_key_path
        self.client = None

    def connect(self):
        """Establish connection to cluster master"""
        try:
            logger.info(f"Establishing connection to {self.host}")
            self.client = SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.client.connect(self.host,
                                username=self.user,
                                key_filename=self.ssh_key_path,
                                look_for_keys=True,
                                timeout=5000)
        except AuthenticationException as e:
            logger.info("Auth failed! Please check your SSH key")
            logger.error(e)
            raise e
        finally:
            logger.info(f"Successfully connected to {self.host}!")
            return self.client

    def disconnect(self):
        """Close SSH connection"""
        self.client.close()


def pytorch_launch_cmd(n_nodes=1, node_rank=0, n_gpus=1, master_ip="127.0.0.1",
                       master_port=1234, training_script=None, training_args={}):
    if training_script is None:
        raise ValueError("No training script provided")

    training_argus = []
    for arg, value in training_args.items():
        argu = f"--{arg} {value}"
        training_argus.append(argu)
    
    training_argus = " ".join(training_argus)

    cmd = f"""python -m torch.distributed.launch \
        --nproc_per_node={n_gpus} \
        --nnodes={n_nodes} \
        --node_rank={node_rank} \
        --master_addr="{master_ip}" \
        --master_port={master_port} \
        {training_script} {training_argus}
    """

    return cmd
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--key", required=True, help="Location of ssh key for EC2 instances")
    parser.add_argument("-a", "--artifacts", required=True, help="Location of cluster artifacts")
    parser.add_argument("-p", "--master-port", default=1234, help="Port on master node for distributed handshakes")
    parser.add_argument("--username", default="ubuntu", help="Username on cluster nodes")

    args = parser.parse_args()

    # Starting jobs
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing job on EC2 cluster...")

    # Load all IPs to SSH into
    with open(os.path.join(args.artifacts, "master_public.txt"), 
              "r", encoding="utf-8") as ip_f:
        master_ip = ip_f.readlines()[0].strip()[1:-1]

    worker_ips = []
    with open(os.path.join(args.artifacts, "worker_public.txt"),
              "r", encoding="utf-8") as ip_f:
        for ip_line in ip_f:
            ip = ip_line.strip()[1:-1]
            worker_ips.append(ip)

    # Establish SSH connections
    ssh_client = ClusterSSHClient(host="54.145.148.154",
                                  user=args.username,
                                  ssh_key_path=args.key)
    ssh_conn = ssh_client.connect()
    
    # TEST
    stdi, stdo, stde = ssh_conn.exec_command("cd what")
    print(type(stdi))
    print(type(stdo))
    print(type(stde))

    print(stdo.readlines())
    print(stde.readlines())



    ssh_client.disconnect()
