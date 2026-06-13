"""
Acces aux donnees pour l'authentification : users et sessions.

On stocke le HASH du token (pas le token brut) dans la table sessions :
si la base fuit, les tokens ne sont pas directement exploitables.
"""
from __future__ import annotations

import time
from typing import Optional

from common import security
from common.database import get_connection


def create_user(login: str, password: str, role: str) -> None:
    """Cree un utilisateur avec un mot de passe hache."""
    pwd_hash = security.hash_password(password)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (login, password_hash, role) VALUES (?, ?, ?)",
            (login, pwd_hash, role),
        )


def user_exists(login: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE login = ?", (login,)
        ).fetchone()
        return row is not None


def get_user(login: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT login, password_hash, role FROM users WHERE login = ?",
            (login,),
        ).fetchone()
        return dict(row) if row else None


def verify_credentials(login: str, password: str) -> Optional[dict]:
    """Renvoie {login, role} si les identifiants sont valides, sinon None."""
    user = get_user(login)
    if user is None:
        # On hache quand meme pour egaliser le temps de reponse (anti enumeration).
        security.hash_password("dummy_password_to_equalize_timing")
        return None
    if not security.verify_password(password, user["password_hash"]):
        return None
    return {"login": user["login"], "role": user["role"]}


def store_session(token: str, login: str, role: str, ttl_seconds: int) -> None:
    """Enregistre une session active (on stocke le hash du token)."""
    now = time.time()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions "
            "(token_hash, login, role, issued_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (security.hash_token(token), login, role, now, now + ttl_seconds),
        )


def lookup_session(token: str) -> Optional[dict]:
    """Renvoie {login, role} si le token est valide et non expire, sinon None."""
    token_hash = security.hash_token(token)
    now = time.time()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT login, role, expires_at FROM sessions WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] < now:
            # Session expiree : on la supprime.
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            return None
        return {"login": row["login"], "role": row["role"]}


def revoke_session(token: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (security.hash_token(token),),
        )
