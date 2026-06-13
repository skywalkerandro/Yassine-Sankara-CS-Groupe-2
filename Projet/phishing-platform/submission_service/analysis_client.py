"""
Client Pyro5 resilient vers AnalysisService.

Encapsule l'appel RPC avec :
- un TIMEOUT (exigence de l'enonce) via Pyro5.config.COMMTIMEOUT
- la gestion propre de l'indisponibilite du service (exception -> erreur geree)

L'appelant (la Gateway) n'a ainsi jamais a connaitre les details de Pyro5.
"""
from __future__ import annotations

import Pyro5.api
import Pyro5.errors

from common import config


class AnalysisUnavailable(Exception):
    """AnalysisService est injoignable ou n'a pas repondu a temps."""


# Timeout global des communications Pyro5 (en secondes).
Pyro5.config.COMMTIMEOUT = config.REMOTE_CALL_TIMEOUT


def analyze_email(sender: str, subject: str, body: str,
                  urls: list, has_attachment: bool = False) -> dict:
    """
    Appelle la methode distante analyze_email. Ouvre un proxy neuf a chaque
    appel (simple et robuste pour une demo ; evite les soucis de thread-safety
    d'un proxy partage).
    """
    try:
        with Pyro5.api.Proxy(config.ANALYSIS_URI) as proxy:
            return proxy.analyze_email(sender, subject, body, urls, has_attachment)
    except Pyro5.errors.TimeoutError as exc:
        raise AnalysisUnavailable("Delai depasse en contactant AnalysisService.") from exc
    except Pyro5.errors.CommunicationError as exc:
        raise AnalysisUnavailable("AnalysisService est injoignable.") from exc
    except Pyro5.errors.PyroError as exc:
        raise AnalysisUnavailable("Erreur lors de l'appel a AnalysisService.") from exc


def ping() -> bool:
    """Verifie la disponibilite du service (utilise pour un health-check)."""
    try:
        with Pyro5.api.Proxy(config.ANALYSIS_URI) as proxy:
            return proxy.ping() == "ok"
    except Pyro5.errors.PyroError:
        return False
