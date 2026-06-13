"""
API Gateway / SubmissionService : point d'entree unique du client.

C'est l'orchestrateur. Il ne contient pas de logique d'analyse ni de gestion
de mots de passe : il DELEGUE aux services specialises, ce qui illustre la
separation des responsabilites d'une architecture repartie.

Flux d'une soumission :
  Client --HTTP/JSON--> Gateway
  Gateway --HTTP/JSON--> AuthService   (verifier le token)
  Gateway --RPC Pyro5--> AnalysisService (calculer le score)
  Gateway --HTTP/JSON--> AuditService  (tracer l'evenement)
  Gateway --SQLite-----> reports       (persister le signalement)

Routes (toutes en JSON) :
- POST /login            : proxy transparent vers AuthService
- POST /submit           : soumettre un e-mail (authentifie)
- POST /reports/list     : lister (authentifie)
- POST /reports/get      : detail d'un signalement (authentifie)
- POST /reports/search   : recherche (authentifie)
- POST /audit/list       : journal d'audit (ADMIN uniquement)
- GET  /health           : etat des dependances
"""
from __future__ import annotations

from common import config
from common.http_client import post_json, RemoteError, ServiceTimeout, ServiceUnavailable
from common.logging_setup import get_logger
from common.service_base import Router, run_server
from common.validation import (
    validate_sender, validate_subject, validate_body, validate_urls,
)

from submission_service import repository
from submission_service.analysis_client import analyze_email, AnalysisUnavailable, ping as analysis_ping
from submission_service.auth_client import require_auth, require_role, AuthUnavailable
from submission_service.audit_client import record as audit_record

logger = get_logger("submission_service")
router = Router("submission_service", logger)


@router.route("POST", "/login")
def login(body: dict, headers: dict):
    """
    Proxy vers AuthService. La Gateway ne verifie pas elle-meme le mot de passe :
    elle transmet la demande au service competent et relaie la reponse.
    """
    try:
        result = post_json(f"{config.AUTH_URL}/login", {
            "login": body.get("login"),
            "password": body.get("password"),
        })
        return 200, result
    except ServiceUnavailable:
        return 503, {"error": "Service d'authentification indisponible."}
    except ServiceTimeout:
        return 504, {"error": "Service d'authentification : delai depasse."}
    except RemoteError as exc:
        # AuthService a renvoye une erreur (ex: 401 identifiants invalides).
        status = getattr(exc, "status", 401)
        return status, getattr(exc, "body", {"error": "Identifiants invalides."})


@router.route("POST", "/submit")
def submit(body: dict, headers: dict):
    """Soumet un e-mail suspect : auth -> validation -> analyse RPC -> stockage -> audit."""
    session = require_auth(headers)  # leve PermissionError si non authentifie
    actor = session["login"]

    # Validation stricte cote serveur (defense en profondeur).
    sender = validate_sender(body.get("sender"))
    subject = validate_subject(body.get("subject", ""))
    text = validate_body(body.get("body", ""))
    urls = validate_urls(body.get("urls", []), text)
    has_attachment = bool(body.get("has_attachment", False))

    # Appel RPC a AnalysisService, avec gestion de l'indisponibilite.
    try:
        analysis = analyze_email(sender, subject, text, urls, has_attachment)
    except AnalysisUnavailable:
        audit_record(actor, "submit", "failure", "AnalysisService indisponible")
        return 503, {"error": "Service d'analyse temporairement indisponible."}

    justification = " ; ".join(analysis["reasons"])
    report_id = repository.save_report(
        sender, subject, text, urls, actor,
        analysis["score"], analysis["level"], justification,
    )

    audit_record(actor, "submit", "success",
                 f"report#{report_id} level={analysis['level']}")
    logger.info("report_created",
                data={"id": report_id, "actor": actor, "level": analysis["level"]})

    return 200, {
        "id": report_id,
        "score": analysis["score"],
        "level": analysis["level"],
        "reasons": analysis["reasons"],
        "indicators": analysis["indicators"],
    }


@router.route("POST", "/reports/list")
def reports_list(body: dict, headers: dict):
    require_auth(headers)
    limit = body.get("limit", 50)
    if not isinstance(limit, int) or not (1 <= limit <= 500):
        limit = 50
    return 200, {"reports": repository.list_reports(limit)}


@router.route("POST", "/reports/get")
def reports_get(body: dict, headers: dict):
    require_auth(headers)
    report_id = body.get("id")
    if not isinstance(report_id, int):
        return 400, {"error": "Identifiant invalide."}
    report = repository.get_report(report_id)
    if report is None:
        return 404, {"error": "Signalement introuvable."}
    return 200, {"report": report}


@router.route("POST", "/reports/search")
def reports_search(body: dict, headers: dict):
    require_auth(headers)
    sender = str(body.get("sender", ""))[:320]
    level = str(body.get("level", ""))[:16]
    keyword = str(body.get("keyword", ""))[:128]
    if level and level not in ("faible", "moyen", "eleve"):
        level = ""
    results = repository.search_reports(sender, level, keyword)
    return 200, {"reports": results}


@router.route("POST", "/audit/list")
def audit_list(body: dict, headers: dict):
    """Consultation du journal d'audit : reservee aux administrateurs."""
    require_role(headers, config.ROLE_ADMIN)  # 403 si pas admin
    limit = body.get("limit", 50)
    if not isinstance(limit, int) or not (1 <= limit <= 500):
        limit = 50
    try:
        result = post_json(f"{config.AUDIT_URL}/list", {"limit": limit})
        return 200, result
    except RemoteError:
        return 503, {"error": "Service d'audit indisponible."}


@router.route("GET", "/health")
def health(body: dict, headers: dict):
    """Etat des dependances (pour la demo de resilience)."""
    auth_ok = audit_ok = False
    try:
        post_json(f"{config.AUTH_URL}/verify", {"token": "healthcheck"})
        auth_ok = True
    except RemoteError:
        pass
    try:
        post_json(f"{config.AUDIT_URL}/list", {"limit": 1})
        audit_ok = True
    except RemoteError:
        pass
    return 200, {
        "gateway": "ok",
        "auth_service": "ok" if auth_ok else "down",
        "audit_service": "ok" if audit_ok else "down",
        "analysis_service": "ok" if analysis_ping() else "down",
    }


def main():
    from common.database import init_db
    init_db()
    run_server(config.GATEWAY_HOST, config.GATEWAY_PORT, router)


if __name__ == "__main__":
    main()
