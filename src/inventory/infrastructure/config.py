"""Infrastructure configuration.

Reads environment variables and configures the database connection.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Database
POS_DB_HOST = os.getenv("POS_DB_HOST", "localhost")
POS_DB_PORT = int(os.getenv("POS_DB_PORT", "5432"))
POS_DB_NAME = os.getenv("POS_DB_NAME", "")
POS_DB_USER = os.getenv("POS_DB_USER", "")
POS_DB_PASSWORD = os.getenv("POS_DB_PASSWORD", "")

# Business configuration
MASTER_SEED = int(os.getenv("MASTER_SEED", "42"))
MAX_STOCK = int(os.getenv("MAX_STOCK", "450"))
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.03"))
ENABLE_NEGATIVE_INVENTORY = os.getenv("ENABLE_NEGATIVE_INVENTORY", "true").lower() == "true"

_VALID_TOKENS_RAW = os.getenv("VALID_TOKENS", "token-seller-123,bearer-token-mercaandes-2026,test-token")
VALID_TOKENS = [t.strip() for t in _VALID_TOKENS_RAW.split(",") if t.strip()]

if not 0 <= ERROR_RATE <= 1:
    raise ValueError("ERROR_RATE must be between 0 and 1.")
