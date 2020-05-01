import torch
import torch.nn as nn

"""
Implements a DCGAN from the paper of Radford, Metz, and Chintala (2015)
"""

class BaseNet(nn.Module):
    def _initialize(self):
        for m in self.modules():
            classname = m.__class__.__name__

            if "Conv" in classname:
                m.weight.data.normal_(0.0, 0.02)
            elif "BatchNorm" in classname:
                m.weight.data.normal_(1.0, 0.02)
                m.bias.data.fill_(0)

    def forward(self, x):
        return x

class GNet(BaseNet):
    """
    Generator of DCGAN.

    :param int z_dim: Latent dimension
    :param int n_filter: Multiplicative filter constant
    :param int n_channel: Number of channels in images
    """

    def __init__(self, z_dim, n_filter, n_channel):
        super(GNet, self).__init__()
        self.net = nn.Sequential(
            nn.ConvTranspose2d(in_channels=z_dim, out_channels=n_filter * 8, kernel_size=4, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(n_filter * 8),
            nn.ReLU(),
            nn.ConvTranspose2d(in_channels=n_filter * 8, out_channels=n_filter * 4, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter * 4),
            nn.ReLU(),
            nn.ConvTranspose2d(in_channels=n_filter * 4, out_channels=n_filter * 2, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter * 2),
            nn.ReLU(),
            nn.ConvTranspose2d(in_channels=n_filter * 2, out_channels=n_filter, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter),
            nn.ReLU(),
            nn.ConvTranspose2d(in_channels=n_filter, out_channels=n_channel, kernel_size=4, stride=2, padding=1, bias=False),
            nn.Tanh()
        )

        self._initialize()

    def forward(self, x):
        return self.net(x)

class DNet(BaseNet):
    """
    Discriminator of DCGAN

    :param int n_filter: Multiplicative filter constant
    :param int n_channel: Number of channels in images
    """

    def __init__(self, n_filter, n_channel):
        super(DNet, self).__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels=n_channel, out_channels=n_filter, kernel_size=4, stride=2, padding=1, bias=False),
            nn.LeakyReLU(0.2),
            nn.Conv2d(in_channels=n_filter, out_channels=n_filter * 2, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter * 2),
            nn.LeakyReLU(0.2),
            nn.Conv2d(in_channels=n_filter * 2, out_channels=n_filter * 4, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter * 4),
            nn.LeakyReLU(0.2),
            nn.Conv2d(in_channels=n_filter * 4, out_channels=n_filter * 8, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(n_filter * 8),
            nn.LeakyReLU(0.2),
            nn.Conv2d(in_channels=n_filter * 8, out_channels=1, kernel_size=4, stride=1, padding=0, bias=False),
            nn.Sigmoid()
        )

        self._initialize()

    def forward(self, x):
        return self.net(x).view(-1, 1).squeeze(-1)
