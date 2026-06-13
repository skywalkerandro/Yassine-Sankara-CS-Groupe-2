"""
Validation et nettoyage des entrees cote serveur.

Principe : NE JAMAIS faire confiance aux donnees venant du client.
On verifie le type, la taille (limites de config -> anti-abus) et le contenu
(caracteres de controle retires). En cas d'entree invalide -> ValidationError.
"""
from __future__ import annotations

import re
from typing import Any

from common import config


class ValidationError(Exception):
    """Erreur levee quand une entree ne respecte pas les regles."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Champ '{field}' invalide : {reason}")


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)


def _strip_control_chars(text: str) -> str:
    return _CONTROL_CHARS.sub("", text)


def require_str(value: Any, field: str, max_len: int, *, allow_empty: bool = False) -> str:
    """Valide une chaine, la nettoie, verifie la longueur. Renvoie la chaine nettoyee."""
    if not isinstance(value, str):
        raise ValidationError(field, "type attendu : chaine de caracteres")
    cleaned = _strip_control_chars(value).strip()
    if not allow_empty and cleaned == "":
        raise ValidationError(field, "valeur vide non autorisee")
    if len(cleaned) > max_len:
        raise ValidationError(field, f"taille maximale depassee ({max_len})")
    return cleaned


def validate_login(value: Any) -> str:
    login = require_str(value, "login", config.MAX_LOGIN_LEN)
    if not re.fullmatch(r"[A-Za-z0-9._@-]+", login):
        raise ValidationError("login", "caracteres non autorises")
    return login


def validate_password(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("password", "type attendu : chaine de caracteres")
    if value == "":
        raise ValidationError("password", "valeur vide non autorisee")
    if len(value) > config.MAX_PASSWORD_LEN:
        raise ValidationError("password", f"taille maximale depassee ({config.MAX_PASSWORD_LEN})")
    return value


def validate_sender(value: Any) -> str:
    sender = require_str(value, "sender", config.MAX_SENDER_LEN)
    if not _EMAIL_RE.match(sender):
        raise ValidationError("sender", "format d'adresse e-mail invalide")
    return sender.lower()


def validate_subject(value: Any) -> str:
    return require_str(value, "subject", config.MAX_SUBJECT_LEN, allow_empty=True)


def validate_body(value: Any) -> str:
    return require_str(value, "body", config.MAX_BODY_LEN, allow_empty=True)


def validate_urls(value: Any, body: str = "") -> list[str]:
    """Valide une liste d'URLs + completion avec celles detectees dans le corps."""
    urls: list[str] = []
    if value is None:
        value = []
    if not isinstance(value, list):
        raise ValidationError("urls", "type attendu : liste")
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("urls", "chaque URL doit etre une chaine")
        cleaned = _strip_control_chars(item).strip()
        if cleaned:
            urls.append(cleaned)
    urls.extend(_URL_RE.findall(body or ""))
    seen = set()
    unique: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
        if len(unique) >= config.MAX_URLS:
            break
    return unique


def extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text or "")
