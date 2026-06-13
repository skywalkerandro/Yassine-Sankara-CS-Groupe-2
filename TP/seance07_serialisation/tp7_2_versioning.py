"""
TP7.2 — Versioning JSON (compatibilité)
========================================
Faire évoluer le payload Document de v1 vers v2 SANS casser la lecture.

  v1 : {id, title, author}
  v2 : ajoute "tags" (list) et "classification" (str, allowlist)

Règles de compatibilité :
  - Ajout de champ optionnel  : OK
  - Retrait de champ          : INTERDIT
  - Changement de type        : INTERDIT

Stratégie : un désérialiseur v2 unique, tolérant, qui accepte aussi les
payloads v1 (champs manquants -> valeurs par défaut).

Décision sur les champs inconnus : on les IGNORE (tolérance), MAIS on les
journalise. Justification : la tolérance aux champs inconnus est ce qui
permet à un lecteur ancien de survivre à un producteur récent (forward
compat). On loggue pour garder une trace en cas d'abus.

Exécution :
    python3 tp7_2_versioning.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tp7_2")

CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}

# Champs connus du schéma v2 (sert à détecter les champs inconnus)
KNOWN_FIELDS = {"id", "title", "author", "tags", "classification"}

# Valeurs par défaut pour les champs ajoutés en v2
DEFAULT_TAGS: list[str] = []
DEFAULT_CLASSIFICATION = "internal"


class ValidationError(Exception):
    """Message générique destiné au client."""


@dataclass
class DocumentV2:
    id: int
    title: str
    author: str
    tags: list[str] = field(default_factory=list)
    classification: str = DEFAULT_CLASSIFICATION


def deserialize_document_v2(raw: str) -> DocumentV2:
    """Désérialiseur v2 rétro-compatible v1.

    - payload v1 (sans tags/classification) -> défauts appliqués
    - payload v2 valide -> objet complet
    - valeur hors allowlist -> rejet (fail closed)
    - champ inconnu -> ignoré mais loggué
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON malformé: %s", exc)
        raise ValidationError("Format JSON invalide")

    if not isinstance(data, dict):
        logger.warning("Racine non-objet: %s", type(data))
        raise ValidationError("Données invalides")

    # Champs inconnus -> tolérés mais signalés
    unknown = set(data.keys()) - KNOWN_FIELDS
    if unknown:
        logger.info("Champs inconnus ignorés (forward-compat): %s", sorted(unknown))

    # --- Champs obligatoires (présents en v1 ET v2) ---
    doc_id = data.get("id")
    if not isinstance(doc_id, int) or isinstance(doc_id, bool) or doc_id <= 0:
        logger.warning("id invalide: %r", doc_id)
        raise ValidationError("Données invalides")

    title = data.get("title")
    if not isinstance(title, str) or not (1 <= len(title.strip()) <= 200):
        logger.warning("title invalide: %r", title)
        raise ValidationError("Données invalides")

    author = data.get("author")
    if not isinstance(author, str) or not (1 <= len(author.strip()) <= 100):
        logger.warning("author invalide: %r", author)
        raise ValidationError("Données invalides")

    # --- Champs v2 (optionnels, défauts si absents = compat v1) ---
    tags = data.get("tags", DEFAULT_TAGS)
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        logger.warning("tags invalide: %r", tags)
        raise ValidationError("Données invalides")

    classification = data.get("classification", DEFAULT_CLASSIFICATION)
    if classification not in CLASSIFICATIONS:
        # Valeur présente mais hors allowlist => on REFUSE (sécurité)
        logger.warning("classification hors allowlist: %r", classification)
        raise ValidationError("Données invalides")

    return DocumentV2(
        id=doc_id,
        title=title.strip(),
        author=author.strip(),
        tags=list(tags),
        classification=classification,
    )


# --------------------------------------------------------------------------- #
# Matrice de compatibilité
# --------------------------------------------------------------------------- #
def _run_matrix() -> None:
    print("=" * 78)
    print("TP7.2 — Matrice de compatibilité (lecteur v2)")
    print("=" * 78)

    matrix = [
        ("payload v1 lu par v2",
         '{"id":1,"title":"X","author":"A"}',
         "ACCEPTE", "champs manquants -> défauts"),

        ("payload v2 complet",
         '{"id":1,"title":"X","author":"A","tags":[],"classification":"public"}',
         "ACCEPTE", "tous champs valides"),

        ("v2 altéré (classification hors allowlist)",
         '{"id":1,"title":"X","author":"A","classification":"top_secret"}',
         "REJETE", "injection de classification bloquée"),

        ("v2 + champ inconnu (priority)",
         '{"id":1,"title":"X","author":"A","priority":"urgent"}',
         "ACCEPTE", "champ inconnu ignoré + loggué"),
    ]

    print(f"\n{'Cas':<42}{'Attendu':<10}{'Obtenu'}")
    print("-" * 78)
    for desc, payload, expected, _reason in matrix:
        try:
            doc = deserialize_document_v2(payload)
            got = "ACCEPTE"
            detail = f"-> {doc}"
        except ValidationError as exc:
            got = "REJETE"
            detail = f"(client: '{exc}')"
        flag = "✓" if got == expected else "✗"
        print(f"{flag} {desc:<40}{expected:<10}{got}")
        print(f"    {detail}")

    print("\n" + "=" * 78)
    print("Conclusion versioning")
    print("=" * 78)
    print(
        "Un lecteur v2 lit les anciens (v1) en appliquant des défauts, et survit\n"
        "aux producteurs plus récents en ignorant les champs qu'il ne connaît pas.\n"
        "La seule chose qui provoque un REJET est une valeur explicitement hors\n"
        "contrat (allowlist) ou un type incorrect : on échoue fermé (fail closed)."
    )


if __name__ == "__main__":
    _run_matrix()
