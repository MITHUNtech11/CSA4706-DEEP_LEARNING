"""
Central configuration for the Secure RAG Hospital RBAC system.
Supports environment variables and .env configuration files with production validation.
"""

import os
import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
POLICIES_DIR = BASE_DIR / "policies"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_env_file():
    """Simple, zero-dependency .env file parser."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v


_load_env_file()

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# Database & Storage Paths
DB_PATH = DATA_DIR / "hospital.db"
ACTIVE_POLICY_PATH = POLICIES_DIR / "policy_v1.0.json"
DRAFT_POLICY_PATH = POLICIES_DIR / "policy_v1.1_draft.json"
PROMPT_TEMPLATE_PATH = TEMPLATES_DIR / "system_prompt_v1.jinja2"
AUDIT_LOG_PATH = LOGS_DIR / "audit_chain.jsonl"
SQLITE_WAL_MODE = os.getenv("SQLITE_WAL_MODE", "true").lower() in ("true", "1", "yes")

# JWT Token Security Settings
DEFAULT_DEV_SECRET = "hospital_rag_secure_hmac_secret_key_2026_capstone_csa47"
JWT_SECRET = os.getenv("JWT_SECRET", DEFAULT_DEV_SECRET)

if ENVIRONMENT == "production" and JWT_SECRET == DEFAULT_DEV_SECRET:
    raise ValueError(
        "CRITICAL SECURITY CONFIGURATION ERROR: Default development JWT_SECRET is prohibited in production mode. "
        "Set a strong secret key in your environment or .env file."
    )

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "hospital-identity-provider"
JWT_AUDIENCE = "hospital-rag-engine"
TOKEN_EXPIRY_MINUTES = int(os.getenv("TOKEN_EXPIRY_MINUTES", "60"))
BREAK_GLASS_EXPIRY_MINUTES = int(os.getenv("BREAK_GLASS_EXPIRY_MINUTES", "15"))

# CORS Origins
raw_cors = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [orig.strip() for orig in raw_cors.split(",") if orig.strip()]

# LLM Configuration
DEFAULT_LLM_MODE = os.getenv("LLM_PROVIDER", "mock").lower()

# Structured Logging Configuration
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "system.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("HospitalRAG")
