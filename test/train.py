import argparse
import os
import logging

import torch
import torch.distributed as distr
import torch.nn as nn

import torchvision.datasets as datasets
import torchvision.models as models
import torchvision.transforms as transforms

from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from tqdm import tqdm

from nets import DNet, GNet
from utils import get_CIFAR10_data

logger = logging.getLogger("dcgan")
logger.setLevel(logging.INFO)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", type=str, default="data/", help="Path to folder where data is stored/downloaded")
    parser.add_argument("--n-workers", type=int, default=4, help="Number of workers for dataloader")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for input")
    parser.add_argument("--z-dim", type=int, default=100, help="Latent space dimension")
    parser.add_argument("--n-filter", type=int, default=16, help="Multiplicative factor for filter size")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.0005, help="Learning rate")
    parser.add_argument("--local_rank", type=int, default=-1, help="Local rank of process. Needed for torch.distributed.launch")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    # Set distributed flag
    distributed = args.local_rank != -1
    device = torch.device(f"cuda:{args.local_rank}" if (torch.cuda.is_available() & distributed) else "cpu")

    if distributed:
        logger.info("Starting distributed training...")
        distr.init_process_group(backend="nccl", init_method="env://")

    ### DATA
    # Get CIFAR10 data
    logger.info("Fetching CIFAR10 data...")
    dset = get_CIFAR10_data(args.data)
    
    # Set (distributed) dataloader
    dsampler = DistributedSampler(dset,) if distributed else None
    dloader = DataLoader(dataset=dset,
                         batch_size=args.batch_size,
                         shuffle=(dsampler is None),
                         sampler=dsampler,
                         num_workers=args.n_workers,
                         pin_memory=True)

    ### MODEL
    N_CHANNEL = 3

    # Set DCGAN model
    gnet = GNet(z_dim=args.z_dim, n_filter=args.n_filter, n_channel=N_CHANNEL)
    dnet = DNet(n_filter=args.n_filter, n_channel=N_CHANNEL)

    # Set loss function and optimizer
    loss_fn = nn.BCELoss()
    optimizer_g = torch.optim.Adam(gnet.parameters(), lr=args.lr, betas=(0.1, 0.999))
    optimizer_d = torch.optim.Adam(dnet.parameters(), lr=args.lr, betas=(0.1, 0.999))

    