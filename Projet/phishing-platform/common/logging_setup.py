"""
Journalisation structuree (logs JSON, une ligne par evenement).

JSON structure : lisible par un humain ET exploitable par une machine.
Chaque service ecrit dans son propre fichier ET sur la console.
Securite : jamais de mot de passe, jamais de token complet (passer par mask_token).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from common.config import LOG_DIR


class JsonFormatter(logging.Formatter):
    """Formate chaque enregistrement de log en une ligne JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", record.name),
            "event": record.getMessage(),
        }
        data = getattr(record, "data", None)
        if isinstance(data, dict):
            payload["data"] = data
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class _ServiceLoggerAdapter(logging.LoggerAdapter):
    """Injecte le nom du service et accepte logger.info('x', data={...})."""

    def __init__(self, logger: logging.Logger, service_name: str):
        super().__init__(logger, {})
        self.service_name = service_name

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.setdefault("service", self.service_name)
        if "data" in kwargs:
            extra["data"] = kwargs.pop("data")
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(service_name: str):
    """Logger configure pour un service : ecrit dans data/logs/<service>.log + console."""
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return _ServiceLoggerAdapter(logger, service_name)
    logger.setLevel(logging.INFO)
    formatter = JsonFormatter()
    log_file = LOG_DIR / f"{service_name}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False
    return _ServiceLoggerAdapter(logger, service_name)
