import argparse
import os
import logging
from tqdm import tqdm

import torch
import torch.distributed as distr
import torch.nn as nn

import torchvision.datasets as datasets
import torchvision.models as models
import torchvision.transforms as transforms

from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP

from ignite.contrib.handlers import ProgressBar
from ignite.engine import Engine, Events
from ignite.handlers import Timer
from ignite.metrics import RunningAverage

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

    def update(engine, batch):
        imgs, _ = batch
        imgs = imgs.to(device)

        # train discriminator
        optimizer_d.zero_grad()

        y_real = dnet.forward(imgs)
        real_labels_d = torch.ones(args.batch_size).to(device)
        loss_dreal = loss_fn(y_real, real_labels_d)

        z_noise = torch.randn(args.batch_size, args.z_dim, 1, 1).to(device)
        fake_imgs = gnet.forward(z_noise)
        y_fake = dnet.forward(fake_imgs.detach())
        fake_labels_d = torch.zeros(args.batch_size).to(device)
        loss_dfake = loss_fn(y_fake, fake_labels_d)

        loss_d = loss_dreal + loss_dfake
        loss_d.backward()
        optimizer_d.step()

        # train generator
        optimizer_g.zero_grad()

        y_fake_g = dnet.forward(fake_imgs)
        fake_labels_g = torch.ones(args.batch_size).to(device)

        loss_g = loss_fn(y_fake_g, fake_labels_g)
        loss_g.backward()
        optimizer_g.step()

        return {"loss_d": loss_d.item(), "loss_g": loss_g.item()}

    logger.info("Constructing training engine...")
    engine = Engine(update)
    timer = Timer(average=True)

    timer.attach(engine,
                 start=Events.EPOCH_STARTED,
                 resume=Events.ITERATION_STARTED,
                 pause=Events.ITERATION_COMPLETED,
                 step=Events.ITERATION_COMPLETED)

    ### TRAINING
    # Attach metrics
    metrics = ["loss_d", "loss_g"]
    RunningAverage(alpha=0.98, output_transform=lambda x: x["loss_d"]).attach(engine, "loss_d")
    RunningAverage(alpha=0.98, output_transform=lambda x: x["loss_g"]).attach(engine, "loss_g")

    pbar = ProgressBar()
    pbar.attach(engine, metric_names=metrics)

    @engine.on(Events.EPOCH_COMPLETED)
    def log_times(engine):
        pbar.log_message(
            "Epoch {} finished: Batch average time is {:.3f}".format(engine.state.epoch, timer.value()))
        timer.reset()

    # Initiate training
    logger.info("Starting training!")
    engine.run(dloader, args.epochs)

    logger.info("Training complete!")

