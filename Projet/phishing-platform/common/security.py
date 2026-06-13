"""
Utilitaires de securite : hachage de mots de passe et gestion des tokens.

Choix techniques expliques :
- Les mots de passe ne sont JAMAIS stockes en clair. On utilise PBKDF2-HMAC-SHA256
  (librairie standard, aucune dependance externe) avec un sel aleatoire par
  utilisateur et un grand nombre d'iterations.
- Les comparaisons de secrets utilisent hmac.compare_digest (anti timing attack).
- Les tokens sont des chaines aleatoires sures (secrets.token_*). On ne journalise
  jamais un token complet : seul un prefixe court est loggable.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from common.config import TOKEN_LOG_PREFIX_LEN

_PBKDF2_ITERATIONS = 200_000
_PBKDF2_ALGO = "sha256"
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hache un mot de passe. Format : pbkdf2_sha256$<iter>$<sel_hex>$<hash_hex>."""
    if not isinstance(password, str) or password == "":
        raise ValueError("Le mot de passe doit etre une chaine non vide.")
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_{_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifie un mot de passe face au hash stocke. Resistant aux timing attacks."""
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    try:
        algo_tag, iter_str, salt_hex, hash_hex = stored.split("$")
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    algo = algo_tag.replace("pbkdf2_", "")
    candidate = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def generate_token() -> str:
    """Genere un token de session aleatoire cryptographiquement sur."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Renvoie le SHA-256 du token. On stocke le hash, jamais le token brut."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def mask_token(token: str) -> str:
    """Version masquee d'un token pour les logs (ne jamais logger le token complet)."""
    if not token:
        return "<vide>"
    prefix = token[:TOKEN_LOG_PREFIX_LEN]
    return f"{prefix}...(masque, {len(token)} car.)"


def constant_time_equals(a: str, b: str) -> bool:
    """Comparaison de deux chaines resistante aux timing attacks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
