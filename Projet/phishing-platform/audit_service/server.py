"""
AuditService : serveur HTTP/JSON de journal d'audit.

Enregistre les evenements de securite (connexions, soumissions, refus d'acces,
erreurs importantes) de maniere centralisee et durable (table audit_events).

Routes :
- POST /record  : {actor, action, outcome, details} -> {ok}
- POST /list    : {limit} -> {events: [...]}  (consultation, usage admin/demo)

Note de securite : ce service ne recoit jamais de mot de passe ni de token brut.
Les details consignes restent factuels et non sensibles.
"""
from __future__ import annotations

from common import config
from common.database import get_connection, init_db
from common.logging_setup import get_logger
from common.service_base import Router, run_server
from common.validation import require_str

logger = get_logger("audit_service")
router = Router("audit_service", logger)

_VALID_OUTCOMES = {"success", "failure", "denied"}


@router.route("POST", "/record")
def record(body: dict, headers: dict):
    actor = require_str(body.get("actor", "anonyme"), "actor", 64, allow_empty=True)
    action = require_str(body.get("action"), "action", 64)
    outcome = require_str(body.get("outcome"), "outcome", 16)
    details = require_str(body.get("details", ""), "details", 512, allow_empty=True)

    if outcome not in _VALID_OUTCOMES:
        outcome = "failure"

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_events (actor, action, outcome, details) "
            "VALUES (?, ?, ?, ?)",
            (actor, action, outcome, details),
        )
    logger.info("audit_recorded", data={"actor": actor, "action": action, "outcome": outcome})
    return 200, {"ok": True}


@router.route("POST", "/list")
def list_events(body: dict, headers: dict):
    limit = body.get("limit", 50)
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        limit = 50
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, actor, action, outcome, details "
            "FROM audit_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return 200, {"events": [dict(r) for r in rows]}


def main():
    init_db()
    run_server(config.AUDIT_HOST, config.AUDIT_PORT, router)


if __name__ == "__main__":
    main()
