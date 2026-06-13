"""
Couche client : appels HTTP/JSON vers l'API Gateway.

Le client ne parle QU'A la Gateway (jamais directement aux autres services) :
c'est le principe du point d'entree unique. Les erreurs reseau sont traduites
en exceptions claires pour l'interface graphique.
"""
from __future__ import annotations

import json
import urllib.request

from common import config
from common.http_client import (
    post_json, HttpStatusError, ServiceUnavailable, ServiceTimeout, RemoteError,
)


class ApiError(Exception):
    """Erreur applicative renvoyee par la Gateway (message affichable)."""


class ApiClient:
    """Petit client conservant le token de session apres connexion."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.GATEWAY_URL
        self.token: str | None = None
        self.login: str | None = None
        self.role: str | None = None

    # --- interne ---
    def _auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _post(self, path: str, payload: dict) -> dict:
        try:
            return post_json(self.base_url + path, payload, headers=self._auth_headers())
        except HttpStatusError as exc:
            msg = "Erreur."
            if isinstance(exc.body, dict):
                msg = exc.body.get("error", msg)
            raise ApiError(msg) from exc
        except ServiceTimeout as exc:
            raise ApiError("Le service met trop de temps a repondre.") from exc
        except ServiceUnavailable as exc:
            raise ApiError("Service injoignable. Les services sont-ils demarres ?") from exc
        except RemoteError as exc:
            raise ApiError("Erreur de communication.") from exc

    # --- API publique ---
    def connect(self, login: str, password: str) -> None:
        result = self._post("/login", {"login": login, "password": password})
        self.token = result["token"]
        self.login = result["login"]
        self.role = result["role"]

    def is_admin(self) -> bool:
        return self.role == config.ROLE_ADMIN

    def submit(self, sender: str, subject: str, body: str,
               urls: list, has_attachment: bool) -> dict:
        return self._post("/submit", {
            "sender": sender, "subject": subject, "body": body,
            "urls": urls, "has_attachment": has_attachment,
        })

    def list_reports(self, limit: int = 50) -> list:
        return self._post("/reports/list", {"limit": limit}).get("reports", [])

    def get_report(self, report_id: int) -> dict:
        return self._post("/reports/get", {"id": report_id}).get("report", {})

    def search_reports(self, sender: str = "", level: str = "", keyword: str = "") -> list:
        return self._post("/reports/search", {
            "sender": sender, "level": level, "keyword": keyword,
        }).get("reports", [])

    def list_audit(self, limit: int = 100) -> list:
        return self._post("/audit/list", {"limit": limit}).get("events", [])

    def health(self) -> dict:
        try:
            with urllib.request.urlopen(self.base_url + "/health", timeout=5) as resp:
                return json.loads(resp.read())
        except Exception:
            return {"gateway": "down"}
