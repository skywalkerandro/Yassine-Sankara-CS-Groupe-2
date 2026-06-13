"""
Client HTTP minimaliste pour les appels JSON entre services.

urllib (librairie standard) : aucune dependance externe.
Resilience :
- TIMEOUT obligatoire sur chaque appel (exigence de l'enonce)
- distinction : service injoignable / timeout / erreur HTTP
- exceptions typees pour une gestion fine cote appelant
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from common.config import REMOTE_CALL_TIMEOUT, MAX_PAYLOAD_BYTES


class RemoteError(Exception):
    """Erreur generique d'appel distant."""


class ServiceUnavailable(RemoteError):
    """Service distant injoignable (connexion refusee, DNS, etc.)."""


class ServiceTimeout(RemoteError):
    """Service distant n'ayant pas repondu dans le delai imparti."""


class HttpStatusError(RemoteError):
    """Service ayant repondu avec un code d'erreur HTTP (4xx/5xx)."""

    def __init__(self, status: int, body: Any):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}")


def post_json(url: str, payload: dict, *, timeout: float = REMOTE_CALL_TIMEOUT,
              headers: dict | None = None) -> dict:
    """
    POST d'un corps JSON, renvoie la reponse JSON.
    Leve ServiceUnavailable / ServiceTimeout / HttpStatusError selon le cas.
    """
    data = json.dumps(payload).encode("utf-8")
    if len(data) > MAX_PAYLOAD_BYTES:
        raise RemoteError("Charge utile trop volumineuse.")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        try:
            err_body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            err_body = {"error": "erreur"}
        raise HttpStatusError(exc.code, err_body) from exc
    except socket.timeout as exc:
        raise ServiceTimeout(f"Delai depasse en contactant {url}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise ServiceTimeout(f"Delai depasse en contactant {url}") from exc
        raise ServiceUnavailable(f"Service injoignable : {url}") from exc
