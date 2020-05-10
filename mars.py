#!/usr/bin/env python3

import argparse
import subprocess as sp
import sys
import os
from pathlib import Path


class MarsCLI:
    """
    Command line interface for interacting with the Mars cluster.
    """

    def __init__(self):
        self.main_arg, self.command_arg = sys.argv[1:2], sys.argv[2:]

        parser = argparse.ArgumentParser(description="Mars cluster CLI tool", 
                                         usage="""mars <command> [<args>]

Commands are as follows:
    create      Creates a Mars cluster of a specified configuration
    connect     Opens an SSH connection to the master node
    destroy     Teardown the cluster
        """)
        parser.add_argument("command", help="Command to use")

        args = parser.parse_args(self.main_arg)
        self.tf_config = {}

        with open(Path(__file__).parent.joinpath("terraform.tfvars"), "r") as f:
            for line in f:
                entry = list(map(lambda x: x.strip(), line.split("=")))
                if len(entry) > 1:
                    self.tf_config[entry[0]] = entry[1]

        if not hasattr(self, args.command):
            print("Unrecognized command")
            parser.print_help()
        else:
            getattr(self, args.command)()

    def create(self):
        parser = argparse.ArgumentParser(
            description="Creates a Mars cluster of a specified configuration",
            usage="mars create -k KEY [<args>]")
        parser.add_argument("-k", "--key", default=None, type=str, help="SSH private key for EC2 nodes")
        parser.add_argument("-t", "--type", default="dask", help="Configuration type of the cluster")
        parser.add_argument("-n", "--num-nodes", default=None, help="Number of worker nodes in cluster")
        parser.add_argument("-i", "--instance", default=None, help="EC2 instance type of nodes")

        args = parser.parse_args(self.command_arg)

        # Fetch missing argument values from terraform.tfvars
        if args.key is None:
            args.key = self.tf_config["key_file"]

        if args.num_nodes is None:
            args.num_nodes = int(self.tf_config["n_workers"])

        if args.instance is None:
            args.instance = self.tf_config["instance_type"]

        filep = Path(__file__).parent.joinpath("scripts/create.sh")
        sp.run([filep, args.key, args.num_nodes, args.instance])



if __name__ == "__main__":
    MarsCLI()
