#/usr/bin/env python3

"""
Initialization script for Mars cluster nodes.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess as sp
import sys

logger = logging.getLogger("init")
logger.setLevel(logging.INFO)

def run_docker_cmd(config, gpu=False, num_gpus=0, nb_pass=None):
    # log into ECR
    sp.run("$(~/.local/bin/aws ecr get-login --no-include-email)", 
           shell=True, 
           env=config["credentials"],
           executable="/bin/bash")

    for img_config in config["images"]:
        cmd = ["docker", "run", "-it", "-d", "--network", "host"]

        if gpu:
            cmd += ["--gpus", "all"]
            cmd += ["-e", f"NUM_GPUS={num_gpus}"]

        for var, val in config["env"].items():
            cmd += ["-e", f"{var}={val}"]

        # if notebook image, set password
        if "notebook" in img_config and bool(img_config["notebook"]):
            cmd += ["-e", f"JUPYTER_PASSWORD={nb_pass}"]
        
        cmd += ["--name", f"{img_config['name']}"]
        # cmd += ["-v", "/opt:/opt"]

        cmd.append(str(img_config["image"]))

        if "command" in img_config:
            cmd.append(str(img_config["command"]))

        # load docker image
        sp.run(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aws-access-key", type=str, required=True, help="AWS access key")
    parser.add_argument("--aws-secret-key", type=str, required=True, help="AWS secret key")
    parser.add_argument("--aws-default-region", type=str, default="us-east-1", help="AWS default region")
    parser.add_argument("--gpu", type=int, default=0, help="GPU instance?")
    parser.add_argument("--num-gpus", type=int, default=0, help="Number of GPUs on EC2 instance")
    parser.add_argument("--nb-pass", type=str, default=None, help="Jupyter notebook password")
    parser.add_argument("--role", type=str, required=True, help="Role-- master or worker?")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Initializing {args.role} node...")

    CONFIG_PATH    = "/opt/config/"
    INIT_PATH      = "/opt/init/"
    ARTIFACTS_PATH = "/opt/artifacts/" 

    ### Initialize
    # Extract config JSON -> dict
    with open(os.path.abspath(os.path.join(CONFIG_PATH, f"{args.role}.json")), "r") as f:
        config = json.load(f)

    if args.role == "worker":
        # Get master address
        with open(os.path.abspath(os.path.join(ARTIFACTS_PATH, "master_private.txt")), "r") as f:
            master_ip_addr = str(f.lines()[0])
            os.environ["MASTER_ADDR"] = master_ip_addr

    # Set environment variables
    logger.info("=> Setting environment variables...")
    for var, value in config["env"].items():
        os.environ[var] = str(value)

    config["credentials"] = {"AWS_ACCESS_KEY_ID": args.aws_access_key,
                             "AWS_SECRET_ACCESS_KEY": args.aws_secret_key,
                             "AWS_DEFAULT_REGION": args.aws_default_region}
    
    # Load docker images
    if isinstance(config["images"], dict):
        config["images"] = [config["images"]]

    run_docker_cmd(config, gpu=args.gpu, num_gpus=args.num_gpus, nb_pass=args.nb_pass)
