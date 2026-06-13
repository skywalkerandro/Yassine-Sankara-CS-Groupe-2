"""
AnalysisService expose via Pyro5 (RPC / objet distant).

C'est le composant qui satisfait l'exigence "au moins un mecanisme RPC ou
objet distant". La Gateway n'appelle PAS ce service en HTTP : elle obtient un
PROXY Pyro5 vers l'objet distant et invoque ses methodes comme si l'objet
etait local. Pyro5 se charge de la serialisation et du transport reseau.

Securite de la serialisation :
- Pyro5 utilise par defaut le serializer 'serpent', qui ne deserialise QUE des
  types de base (pas d'objets arbitraires) -> pas d'execution de code via la
  deserialisation, contrairement a pickle. C'est un choix deliberle.
- On expose une interface minimale (une seule methode metier).
"""
from __future__ import annotations

import Pyro5.api
import Pyro5.server

from common import config
from common.logging_setup import get_logger
from common.validation import (
    validate_sender, validate_subject, validate_body, validate_urls,
)
from analysis_service.engine import analyze

logger = get_logger("analysis_service")


@Pyro5.api.expose
class AnalysisService:
    """Objet distant offrant l'analyse de phishing."""

    def analyze_email(self, sender: str, subject: str, body: str,
                      urls=None, has_attachment: bool = False) -> dict:
        """
        Methode RPC : valide les entrees puis applique le moteur heuristique.
        Renvoie {score, level, reasons, indicators}.

        La validation est refaite ICI meme si la Gateway valide deja : defense
        en profondeur (le service ne fait jamais confiance a son appelant).
        """
        sender = validate_sender(sender)
        subject = validate_subject(subject)
        body = validate_body(body)
        urls = validate_urls(urls or [], body)

        result = analyze(sender, subject, body, urls, bool(has_attachment))
        logger.info(
            "email_analyzed",
            data={"sender": sender, "score": result["score"], "level": result["level"]},
        )
        return result

    def ping(self) -> str:
        """Sonde de disponibilite (sante du service)."""
        return "ok"


def main():
    # Daemon Pyro5 ecoutant sur un port fixe (URI direct, sans name server).
    daemon = Pyro5.server.Daemon(host=config.ANALYSIS_HOST, port=config.ANALYSIS_PORT)
    # On enregistre l'objet avec un identifiant stable correspondant a l'URI.
    daemon.register(AnalysisService(), objectId=config.ANALYSIS_OBJECT_ID)
    logger.info(
        "service_started",
        data={"host": config.ANALYSIS_HOST, "port": config.ANALYSIS_PORT,
              "uri": config.ANALYSIS_URI},
    )
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        logger.info("service_stopping")


if __name__ == "__main__":
    main()
