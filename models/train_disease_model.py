"""
Train the plant-disease classifier on your own labeled image dataset.

Expected folder layout (standard torchvision ImageFolder format):

    data/dataset/
        train/
            healthy/
                img001.jpg
                img002.jpg
            leaf_blight/
                img001.jpg
            powdery_mildew/
                ...
        val/
            healthy/
                ...
            leaf_blight/
                ...

Run:
    python -m models.train_disease_model
    python -m models.train_disease_model --epochs 15 --freeze False
"""

import argparse
import json
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from tqdm import tqdm

from config import (
    DATASET_DIR, MODEL_PATH, CLASS_MAP_PATH,
    IMAGE_SIZE, BATCH_SIZE, NUM_EPOCHS, LEARNING_RATE,
)
from models.disease_cnn import build_model, get_transforms
from utils.logger import get_logger

logger = get_logger("train_disease_model")


def load_datasets():
    train_dir = DATASET_DIR / "train"
    val_dir = DATASET_DIR / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            f"Expected {train_dir} and {val_dir} to exist. "
            "Place your labeled images there, one subfolder per class."
        )

    train_ds = ImageFolder(train_dir, transform=get_transforms(IMAGE_SIZE, train=True))
    val_ds = ImageFolder(val_dir, transform=get_transforms(IMAGE_SIZE, train=False))
    return train_ds, val_ds


def train(epochs: int = NUM_EPOCHS, freeze_backbone: bool = True, lr: float = LEARNING_RATE):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")

    train_ds, val_ds = load_datasets()
    class_names = train_ds.classes
    logger.info(f"Found {len(class_names)} classes: {class_names}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = build_model(num_classes=len(class_names), freeze_backbone=freeze_backbone).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr
    )

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        start = time.time()

        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{epochs} [train]"):
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        train_loss = running_loss / total
        train_acc = correct / total

        val_acc = evaluate(model, val_loader, device)
        elapsed = time.time() - start

        logger.info(
            f"Epoch {epoch}: train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_acc={val_acc:.4f} ({elapsed:.1f}s)"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_PATH)
            CLASS_MAP_PATH.write_text(json.dumps(class_names, indent=2))
            logger.info(f"New best model saved (val_acc={val_acc:.4f}) -> {MODEL_PATH}")

    logger.info(f"Training complete. Best val accuracy: {best_val_acc:.4f}")


def evaluate(model, loader, device) -> float:
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    return correct / total if total else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the plant disease CNN")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument(
        "--freeze", type=lambda x: x.lower() != "false", default=True,
        help="Freeze pretrained backbone (True) or fine-tune all layers (False)",
    )
    args = parser.parse_args()
    train(epochs=args.epochs, freeze_backbone=args.freeze, lr=args.lr)
