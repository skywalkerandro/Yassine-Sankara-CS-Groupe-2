"""
Client vers AuditService. L'audit ne doit JAMAIS faire echouer une operation
metier : si le service d'audit est indisponible, on logge localement et on
continue (l'audit est best-effort cote disponibilite, mais l'echec est trace).
"""
from __future__ import annotations

from common import config
from common.http_client import post_json, RemoteError
from common.logging_setup import get_logger

logger = get_logger("submission_service")


def record(actor: str, action: str, outcome: str, details: str = "") -> None:
    """Envoie un evenement d'audit. N'echoue jamais bruyamment."""
    try:
        post_json(
            f"{config.AUDIT_URL}/record",
            {"actor": actor, "action": action, "outcome": outcome, "details": details},
        )
    except RemoteError:
        # On ne bloque pas l'operation metier ; on garde une trace locale.
        logger.error(
            "audit_unavailable",
            data={"actor": actor, "action": action, "outcome": outcome},
        )
