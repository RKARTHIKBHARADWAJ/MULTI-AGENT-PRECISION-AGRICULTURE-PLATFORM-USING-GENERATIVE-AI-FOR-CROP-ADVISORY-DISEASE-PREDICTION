"""
Disease classification model: transfer learning on top of a pretrained
ResNet18. This is the standard, reliable approach for plant-disease image
datasets (e.g. PlantVillage-style folder layouts) - the pretrained ImageNet
features generalize well to leaf textures/lesions with only a few epochs
of fine-tuning, even on modest dataset sizes.
"""

import torch
import torch.nn as nn
from torchvision import models


def build_model(num_classes: int, freeze_backbone: bool = True) -> nn.Module:
    """
    Returns a ResNet18 with its final FC layer replaced for `num_classes`.
    If freeze_backbone=True, only the new classifier head is trained
    (fast, works well with small datasets). Set False to fine-tune the
    whole network once you have a larger dataset.
    """
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )
    return model


def get_transforms(image_size: int, train: bool):
    """Data augmentation for training, plain resize/normalize for inference."""
    from torchvision import transforms

    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )

    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            normalize,
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            normalize,
        ])
