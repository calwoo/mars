#!/usr/bin/env python3

"""
This programmatically launches a PyTorch distributed training job on a custom EC2 training
cluster.
"""

import argparse
import logging
import multiprocessing as mp
import os
import shutil
import sys
from functools import partial

from fabric import Connection
from fabric.group import Group, ThreadingGroup

logger = logging.getLogger("launch")
logger.setLevel(logging.INFO)


# PyTorch distributed launch command
def pytorch_launch_cmd(n_nodes=1, node_rank=0, n_gpus=1, master_ip="127.0.0.1",
                       master_port=1234, training_path=None, training_args={}):
    """
    String-wrapper for the torch.distributed.launch CLI tool; arguments to the function
    follow the documentation:
        https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py
    
    :param int n_nodes: Number of nodes used for distributed training
    :param int node_rank: Global rank of node for multi-node distribution
    :param int n_gpus: Number of GPUs on node. Each GPU will run a single process
    :param str master_ip: (Private) IP of master node in cluster. Do not put in the
        public IP here as the worker nodes cannot communicate outside the subnet
    :param int master_port: Port exposed on master node for distributed handshakes
    :param str training_path: Path of experiment to run
    :param dict training_args: Dictionary of command line args to be passed to experiment
    :return str: Launch command to be SSHed over
    """

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
        {training_path} {training_argus}
    """

    return cmd

# Load artifact files into a Python dictionary
def load_artifacts(artifact_path):
    """
    Produces a Python dictionary of cluster node IPs, global rank, and number of GPUs.

    :param str artifact_path: Path where cluster artifacts are stored
    :return dict: Dictionary of cluster information
    """

    cluster_arts = {}
    with open(os.path.join(artifact_path, "master_public.txt"), "r", encoding="utf-8") as ip_f:
        cluster_arts["master_pub"] = ip_f.readlines()[0].strip()[1:-1]

    with open(os.path.join(artifact_path, "master_private.txt"), "r", encoding="utf-8") as ip_f:
        cluster_arts["master_pvt"] = ip_f.readlines()[0].strip()[1:-1]

    cluster_arts["worker_pub"] = {}
    with open(os.path.join(artifact_path, "worker_public.txt"), "r", encoding="utf-8") as ip_f:
        for rank, ip_line in enumerate(ip_f):
            ip = ip_line.strip()[1:-1]
            cluster_arts["worker_pub"][rank + 1] = ip

    return cluster_arts

# Pull a git repo/branch onto remote servers
def pull(conn, repo, branch="master", local=True):
    """
    Performs a git pull request on a remote host

    :param conn: Paramiko/fabric SSH connection object
    :param str repo: Git repository to clone
    :param str branch: Specific branch to clone
    :param bool local: Are credentials be local or on remote?
    """

    if local:
        # check if a git-credentials file exists
        cred_path = os.path.expanduser("~/.git-credentials")
        if os.path.isfile(cred_path):
            with open(cred_path, "r") as f:
                cred = f.readlines()[0]
            # set token
            os.environ["GITHUB_TOKEN"] = cred.split(":")[2].split("@")[0]

        # get github token from env
        GITHUB_USER  = "calwoo"
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

        with conn.cd("/opt/"):
            conn.run(f"sudo git clone -b {branch} https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{repo}.git")
    else:
        with conn.cd("/opt/"):
            conn.run(f"sudo git clone -b {branch} https://$GITHUB_USER:$GITHUB_TOKEN@github.com/{repo}.git")

 
    

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
    cluster_info = load_artifacts(args.artifacts)
    cluster_public_ips  = {0: cluster_info["master_pub"], **cluster_info["worker_pub"]}

    # Establish SSH connections
    logger.info("Establishing SSH connections to cluster nodes...")
    cluster_conns = {rank: Connection(host=host,
                                      user=args.username,
                                      connect_kwargs={
                                          "key_filename": args.key
                                      })
                                      for rank, host in cluster_public_ips.items()
                    }

    # pull(conn, "medivo/uwmodels", branch="cwoo-embeddings")
    
    # Run torch.distributed.launch commands all at once
    n_nodes = len(cluster_public_ips)
    n_gpus = 1

    logger.info("Launching distributed training job...")
    with mp.Pool(processes=n_nodes) as pool:
        def mp_wrap(node_rank, conn):
            cmd = pytorch_launch_cmd(n_nodes=n_nodes,
                                     node_rank=node_rank
                                     n_gpus=n_gpus,
                                     master_ip=cluster_info["master_pvt"],
                                     master_port=args.master_port,
                                     training_path="test.py",
                                     training_args={
                                         "lr": 0.001,
                                         "batch-size": 128
                                     })
            return conn.run(cmd)

        _ = pool.map(mp_wrap, cluster_conns.items())

    logger.info("Distributed training is over.")