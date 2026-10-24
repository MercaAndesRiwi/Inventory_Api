"""Inventory API configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

MASTER_SEED = int(os.getenv("MASTER_SEED", "42"))
MAX_STOCK = int(os.getenv("MAX_STOCK", "450"))

if MASTER_SEED <= 0:
    raise ValueError("MASTER_SEED must be a positive integer.")
if MAX_STOCK <= 0:
    raise ValueError("MAX_STOCK must be a positive integer.")
