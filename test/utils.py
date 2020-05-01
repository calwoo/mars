import os

import torchvision.datasets as datasets
import torchvision.transforms as transforms


def get_CIFAR10_data(path):
    """
    :param str path: Path to download the data to
    """

    if not os.path.exists(path):
        os.makedirs(path)

    dset = datasets.CIFAR10(root=path,
                            download=True,
                            transform=transforms.Compose([
                                transforms.Resize(64),
                                transforms.CenterCrop(64),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                            ]))
        
    return dset



    