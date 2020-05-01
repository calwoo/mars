#!/usr/bin/env python3

"""
This programmatically launches a PyTorch distributed training job on a custom EC2 training
cluster.
"""

import argparse
import logging
import os
import shutil
import sys
from functools import partial
from concurrent.futures import ThreadPoolExecutor

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

    if training_path is None:
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

# Wrapped fabric Connection object-- commands are run through a docker exec over SSH
class DConnection:
    """
    Wrapper for the paramiko/fabric Connection object. This automatically pushes
    any command pushed to SSH through to the specified Docker image running on the
    container.

    :param str image: Alias of the Docker image (local name on remote) to remote into
    :param - kwargs: Remaining parameters the same as in fabric
    """

    def __init__(self, image, **kwargs):
        self._conn = Connection(**kwargs)
        self._image = image

    def run(self, cmd, docker=False):
        """
        Runs a command remotely via SSH

        :param str cmd: Command to run
        :param bool docker: Run docker exec?
        """
        
        if docker:
            docker_cmd = f"docker exec {self._image} {cmd}"
            return self._conn.run(docker_cmd)
        else:
            return self._conn.run(cmd)

# Pull a git repo/branch onto remote servers
def pull(conn, repo, branch="master", local=True):
    """
    Performs a git pull request on a remote host

    :param conn: Paramiko/fabric SSH connection object
    :param str repo: Git repository to clone
    :param str branch: Specific branch to clone
    :param bool local: Are credentials local or on remote?
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
    parser.add_argument("-i", "--image", default="cluster_img", help="Docker image alias on remote machine")
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
    cluster_conns = {rank: DConnection(args.image,
                                       host=host,
                                       user=args.username,
                                       connect_kwargs={
                                           "key_filename": args.key
                                       })
                                       for rank, host in cluster_public_ips.items()
                    }

    # Pull from repo from github
    for rank, dconn in cluster_conns.items():
        pull(dconn._conn, "medivo/uwmodels", branch="cwoo-embeddings")
    
    # Run torch.distributed.launch commands all at once
    n_nodes = len(cluster_public_ips)
    n_gpus = "$NUM_GPUS"

    def mp_wrap(tup):
        node_rank, conn = tup
        # cmd = pytorch_launch_cmd(n_nodes=n_nodes,
        #                          node_rank=node_rank,
        #                          n_gpus=n_gpus,
        #                          master_ip=cluster_info["master_pvt"],
        #                          master_port=args.master_port,
        #                          training_path="test.py",
        #                          training_args={
        #                              "lr": 0.001,
        #                              "batch-size": 128
        #                          })
        
        cmd = f"echo \"hello from {node_rank}\""
        logger.info(f"Running job on node {node_rank}...")
        return conn.run(cmd, docker=True)

    logger.info("Launching distributed training job...")

    with ThreadPoolExecutor(max_workers=n_nodes) as pool:
        _ = pool.map(mp_wrap, cluster_conns.items())

    logger.info("Distributed training is over.")