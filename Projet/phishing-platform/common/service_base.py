"""
Socle commun de serveur HTTP/JSON pour les services.

Surcouche au-dessus de http.server (librairie standard) :
- routage simple par (methode, chemin)
- parsing JSON avec LIMITE DE TAILLE (anti-abus)
- limitation du nombre de requetes par IP (rate limiting, fenetre glissante)
- transformation systematique des exceptions en reponses JSON GENERIQUES
  cote client (on ne divulgue pas les details internes)
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from common.config import (
    MAX_PAYLOAD_BYTES,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)
from common.validation import ValidationError

RouteHandler = Callable[[dict, dict], tuple]


class _RateLimiter:
    """Limiteur d'appels par IP, fenetre glissante en memoire. Thread-safe."""

    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_ip: str) -> bool:
        now = time.time()
        with self._lock:
            hits = self._hits[client_ip]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            return True


class Router:
    """Enregistre les routes et fabrique le handler HTTP correspondant."""

    def __init__(self, service_name: str, logger):
        self.service_name = service_name
        self.logger = logger
        self._routes: dict = {}
        self._rate_limiter = _RateLimiter(RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    def add_route(self, method: str, path: str, handler: RouteHandler) -> None:
        self._routes[(method.upper(), path)] = handler

    def route(self, method: str, path: str):
        def decorator(func: RouteHandler) -> RouteHandler:
            self.add_route(method, path, func)
            return func
        return decorator

    def build_handler_class(self):
        router = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass

            def _send_json(self, status: int, payload: dict):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _client_ip(self) -> str:
                return self.client_address[0] if self.client_address else "?"

            def _handle(self, method: str):
                ip = self._client_ip()
                if not router._rate_limiter.allow(ip):
                    router.logger.info("rate_limit_exceeded", data={"ip": ip, "path": self.path})
                    self._send_json(429, {"error": "Trop de requetes."})
                    return
                handler = router._routes.get((method, self.path))
                if handler is None:
                    self._send_json(404, {"error": "Ressource introuvable."})
                    return
                length = int(self.headers.get("Content-Length", 0))
                if length > MAX_PAYLOAD_BYTES:
                    self._send_json(413, {"error": "Charge utile trop volumineuse."})
                    return
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                    if not isinstance(body, dict):
                        raise ValueError("corps JSON invalide")
                except (ValueError, UnicodeDecodeError):
                    self._send_json(400, {"error": "Corps JSON invalide."})
                    return
                try:
                    status, response = handler(body, dict(self.headers))
                    self._send_json(status, response)
                except ValidationError as exc:
                    router.logger.info("validation_error", data={"field": exc.field, "ip": ip})
                    self._send_json(400, {"error": "Entree invalide."})
                except PermissionError:
                    self._send_json(403, {"error": "Acces refuse."})
                except Exception as exc:
                    router.logger.error(
                        "internal_error",
                        data={"path": self.path, "type": type(exc).__name__},
                        exc_info=True,
                    )
                    self._send_json(500, {"error": "Erreur interne du service."})

            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

        return _Handler


def run_server(host: str, port: int, router: Router) -> None:
    """Demarre le serveur HTTP (bloquant) pour un service."""
    handler_class = router.build_handler_class()
    server = ThreadingHTTPServer((host, port), handler_class)
    router.logger.info("service_started", data={"host": host, "port": port})
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        router.logger.info("service_stopping")
    finally:
        server.shutdown()
