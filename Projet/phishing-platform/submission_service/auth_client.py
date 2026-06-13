"""
Client vers AuthService + helpers d'autorisation pour la Gateway.

require_auth() verifie un token aupres d'AuthService et renvoie la session
{login, role}. require_role() ajoute un controle de role. En cas d'echec,
on leve PermissionError -> transformee en 403 generique par le socle serveur.
"""
from __future__ import annotations

from common import config
from common.http_client import post_json, RemoteError


class AuthUnavailable(Exception):
    """AuthService est injoignable."""


def verify_token(token: str) -> dict:
    """
    Demande a AuthService de verifier un token.
    Renvoie {valid: bool, login?, role?}.
    """
    try:
        return post_json(f"{config.AUTH_URL}/verify", {"token": token})
    except RemoteError as exc:
        raise AuthUnavailable("AuthService est injoignable.") from exc


def require_auth(headers: dict) -> dict:
    """
    Extrait le token de l'en-tete Authorization: Bearer <token>, le verifie,
    et renvoie la session. Leve PermissionError si absent/invalide.
    """
    raw = headers.get("Authorization") or headers.get("authorization") or ""
    if not raw.lower().startswith("bearer "):
        raise PermissionError("Token manquant.")
    token = raw.split(" ", 1)[1].strip()

    result = verify_token(token)
    if not result.get("valid"):
        raise PermissionError("Token invalide.")
    return {"login": result["login"], "role": result["role"]}


def require_role(headers: dict, role: str) -> dict:
    """Comme require_auth, mais exige en plus un role precis."""
    session = require_auth(headers)
    if session["role"] != role:
        raise PermissionError("Role insuffisant.")
    return session
