"""
AuthService : serveur HTTP/JSON d'authentification.

Routes :
- POST /login    : {login, password} -> {token, role} ou 401
- POST /verify   : {token} -> {valid, login, role} (utilise par la Gateway)
- POST /logout   : {token} -> {ok}

Securite :
- mots de passe haches (jamais en clair, jamais logges)
- tokens jamais logges en entier (mask_token)
- entrees validees, erreurs generiques cote client
"""
from __future__ import annotations

from common import config
from common.logging_setup import get_logger
from common.security import generate_token, mask_token
from common.service_base import Router, run_server
from common.validation import validate_login, validate_password, require_str

from auth_service import repository

logger = get_logger("auth_service")
router = Router("auth_service", logger)


@router.route("POST", "/login")
def login(body: dict, headers: dict):
    login_value = validate_login(body.get("login"))
    password = validate_password(body.get("password"))

    user = repository.verify_credentials(login_value, password)
    if user is None:
        logger.info("login_failed", data={"login": login_value})
        # Message volontairement generique : on ne dit pas si c'est le login
        # ou le mot de passe qui est faux (anti enumeration de comptes).
        return 401, {"error": "Identifiants invalides."}

    token = generate_token()
    repository.store_session(token, user["login"], user["role"], config.TOKEN_TTL_SECONDS)
    logger.info(
        "login_success",
        data={"login": user["login"], "role": user["role"], "token": mask_token(token)},
    )
    return 200, {"token": token, "role": user["role"], "login": user["login"]}


@router.route("POST", "/verify")
def verify(body: dict, headers: dict):
    token = require_str(body.get("token"), "token", 256)
    session = repository.lookup_session(token)
    if session is None:
        return 200, {"valid": False}
    return 200, {"valid": True, "login": session["login"], "role": session["role"]}


@router.route("POST", "/logout")
def logout(body: dict, headers: dict):
    token = require_str(body.get("token"), "token", 256)
    repository.revoke_session(token)
    logger.info("logout", data={"token": mask_token(token)})
    return 200, {"ok": True}


def main():
    from common.database import init_db
    init_db()
    run_server(config.AUTH_HOST, config.AUTH_PORT, router)


if __name__ == "__main__":
    main()
