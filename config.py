"""
Central configuration for the Precision Agriculture Platform.
All secrets/keys are read from environment variables - never hardcode them.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "data" / "dataset"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(exist_ok=True)
CLASS_MAP_PATH = CHECKPOINT_DIR / "class_mapping.json"
MODEL_PATH = CHECKPOINT_DIR / "disease_model.pt"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_EPOCHS = 10
LEARNING_RATE = 1e-4

SOIL_MOISTURE_LOW = 25.0
SOIL_MOISTURE_HIGH = 80.0
DISEASE_CONFIDENCE_ALERT = 0.60
