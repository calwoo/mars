import argparse
import os

import torch
import torch.distributed as distr
import torch.nn as nn
import torchvision.datasets as datasets
import torchvision.models as models
import torchvision.transforms as transforms
from tqdm import tqdm



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", type=str, default="/data", help="Path to folder where data is stored/downloaded")
    parser.add_argument("--n-workers", type=int, default=4, help="Number of workers for dataloader")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for input")
    parser.add_argument("--z-dim", type=int, default=100, help="Latent space dimension")
    parser.add_argument("--n-filters", type=int, default=16, help="Multiplicative factor for filter size")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.0005, help="Learning rate")

    args = parser.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    