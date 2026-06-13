"""
Configuration centrale de la plateforme.

Toutes les constantes partagees (ports, hotes, limites, chemins) sont
regroupees ici pour eviter la duplication et faciliter la modification.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Chemins ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "platform.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Reseau : API Gateway (HTTP/JSON) -------------------------------------
GATEWAY_HOST = os.environ.get("PHISH_GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.environ.get("PHISH_GATEWAY_PORT", "8000"))
GATEWAY_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}"

# --- Reseau : AuthService (HTTP/JSON) -------------------------------------
AUTH_HOST = os.environ.get("PHISH_AUTH_HOST", "127.0.0.1")
AUTH_PORT = int(os.environ.get("PHISH_AUTH_PORT", "8001"))
AUTH_URL = f"http://{AUTH_HOST}:{AUTH_PORT}"

# --- Reseau : AuditService (HTTP/JSON) ------------------------------------
AUDIT_HOST = os.environ.get("PHISH_AUDIT_HOST", "127.0.0.1")
AUDIT_PORT = int(os.environ.get("PHISH_AUDIT_PORT", "8002"))
AUDIT_URL = f"http://{AUDIT_HOST}:{AUDIT_PORT}"

# --- Reseau : AnalysisService (RPC via Pyro5) -----------------------------
ANALYSIS_HOST = os.environ.get("PHISH_ANALYSIS_HOST", "127.0.0.1")
ANALYSIS_PORT = int(os.environ.get("PHISH_ANALYSIS_PORT", "8003"))
ANALYSIS_OBJECT_ID = "phishing.analysis"
ANALYSIS_URI = f"PYRO:{ANALYSIS_OBJECT_ID}@{ANALYSIS_HOST}:{ANALYSIS_PORT}"

# --- Securite : tokens -----------------------------------------------------
TOKEN_TTL_SECONDS = int(os.environ.get("PHISH_TOKEN_TTL", "3600"))
TOKEN_LOG_PREFIX_LEN = 8

# --- Securite : limites d'entree ------------------------------------------
MAX_LOGIN_LEN = 64
MAX_PASSWORD_LEN = 128
MAX_SENDER_LEN = 320
MAX_SUBJECT_LEN = 512
MAX_BODY_LEN = 20_000
MAX_URLS = 50
MAX_PAYLOAD_BYTES = 64 * 1024

# --- Securite : limitation d'appels (rate limiting) -----------------------
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 60

# --- Resilience ------------------------------------------------------------
REMOTE_CALL_TIMEOUT = float(os.environ.get("PHISH_REMOTE_TIMEOUT", "5.0"))

# --- Roles -----------------------------------------------------------------
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
VALID_ROLES = (ROLE_ADMIN, ROLE_ANALYST)
