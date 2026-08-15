"""
DiseaseAgent - runs the trained CNN on a leaf image and returns the
predicted disease class + confidence. Expects you've already run
`python -m models.train_disease_model` so MODEL_PATH/CLASS_MAP_PATH exist.
"""

import json
from typing import Any, Dict

import torch
from PIL import Image

from agents.base_agent import BaseAgent
from config import MODEL_PATH, CLASS_MAP_PATH, IMAGE_SIZE, DISEASE_CONFIDENCE_ALERT
from models.disease_cnn import build_model, get_transforms


class DiseaseAgent(BaseAgent):
    name = "disease_agent"

    def __init__(self):
        super().__init__()
        self._model = None
        self._class_names = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model(self):
        if self._model is not None:
            return

        if not MODEL_PATH.exists() or not CLASS_MAP_PATH.exists():
            raise FileNotFoundError(
                "No trained model found. Run "
                "'python -m models.train_disease_model' first, "
                "using your labeled image dataset under data/dataset/."
            )

        self._class_names = json.loads(CLASS_MAP_PATH.read_text())
        model = build_model(num_classes=len(self._class_names))
        model.load_state_dict(torch.load(MODEL_PATH, map_location=self._device))
        model.to(self._device)
        model.eval()
        self._model = model

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        image_path = context.get("image_path")
        if not image_path:
            return {}  # disease check optional - just skip if no image given

        self._load_model()

        image = Image.open(image_path).convert("RGB")
        transform = get_transforms(IMAGE_SIZE, train=False)
        tensor = transform(image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            logits = self._model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)
            confidence, idx = torch.max(probs, dim=0)

        predicted_class = self._class_names[idx.item()]
        top3_idx = torch.topk(probs, k=min(3, len(self._class_names))).indices.tolist()
        top3 = [
            {"class": self._class_names[i], "confidence": round(probs[i].item(), 4)}
            for i in top3_idx
        ]

        return {
            "disease_prediction": {
                "predicted_class": predicted_class,
                "confidence": round(confidence.item(), 4),
                "top3": top3,
                "alert": confidence.item() >= DISEASE_CONFIDENCE_ALERT
                and predicted_class.lower() != "healthy",
            }
        }
