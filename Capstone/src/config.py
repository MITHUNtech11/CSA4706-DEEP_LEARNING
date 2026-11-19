"""
Central configuration for the Secure RAG Hospital RBAC system.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
POLICIES_DIR = BASE_DIR / "policies"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "hospital.db"
ACTIVE_POLICY_PATH = POLICIES_DIR / "policy_v1.0.json"
DRAFT_POLICY_PATH = POLICIES_DIR / "policy_v1.1_draft.json"
PROMPT_TEMPLATE_PATH = TEMPLATES_DIR / "system_prompt_v1.jinja2"
AUDIT_LOG_PATH = LOGS_DIR / "audit_chain.jsonl"

# JWT Token Security Settings
JWT_SECRET = "hospital_rag_secure_hmac_secret_key_2026_capstone_csa47"
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "hospital-identity-provider"
JWT_AUDIENCE = "hospital-rag-engine"
TOKEN_EXPIRY_MINUTES = 60
BREAK_GLASS_EXPIRY_MINUTES = 15

# LLM Configuration
# Modes: "mock" (offline deterministic reference), "gemini", "openai"
DEFAULT_LLM_MODE = "mock"
