#!/usr/bin/env python3

import argparse
import sys

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

        if not hasattr(self, args.command):
            print("Unrecognized command")
            parser.print_help()
        else:
            getattr(self, args.command)()

    def create(self):
        parser = argparse.ArgumentParser(
            description="Creates a Mars cluster of a specified configuration",
            usage="mars create -k KEY [<args>]")
        parser.add_argument("-k", "--key", required=True, type=str, help="SSH private key for EC2 nodes")
        parser.add_argument("-t", "--type", default="dask", help="Configuration type of the cluster")

        args = parser.parse_args(self.command_arg)
        print("test creating cluster!")



if __name__ == "__main__":
    MarsCLI()