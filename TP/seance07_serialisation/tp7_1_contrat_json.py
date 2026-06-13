"""
TP7.1 — Contrat JSON + validation stricte (API)
=================================================
Définition d'un contrat JSON formel pour les entités Document et UserPublic,
avec sérialisation, désérialisation et validation stricte ("fail closed").

Principes appliqués :
  - dataclasses pour modéliser les entités
  - serialize_*() exclut tout champ privé/sensible
  - deserialize_*() valide chaque champ de façon exhaustive
  - Message générique côté client, détail complet côté logs serveur
  - "Fail closed" : tout champ non conforme => rejet total

Exécution :
    python3 tp7_1_contrat_json.py
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------- #
# Configuration des logs (audience interne : détail complet)
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("tp7_1")

# Allowlists (référentiels fermés)
CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
ROLES = {"viewer", "editor", "admin"}

# Format ISO 8601 simplifié : YYYY-MM-DDTHH:MM:SSZ
ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


# --------------------------------------------------------------------------- #
# Exception métier : message générique destiné au client
# --------------------------------------------------------------------------- #
class ValidationError(Exception):
    """Erreur de validation — porte un message générique sûr pour le client."""


# --------------------------------------------------------------------------- #
# Entités (dataclasses)
# --------------------------------------------------------------------------- #
@dataclass
class Document:
    id: int
    title: str
    author: str
    tags: list[str] = field(default_factory=list)
    classification: str = "internal"
    created_at: str | None = None


@dataclass
class UserPublic:
    username: str
    display_name: str
    role: str


# --------------------------------------------------------------------------- #
# Helpers de validation (fail closed)
# --------------------------------------------------------------------------- #
def _require(condition: bool, log_msg: str, client_msg: str = "Données invalides") -> None:
    """Lève une ValidationError si la condition n'est pas remplie.

    log_msg  -> détaillé, pour les logs serveur
    client_msg -> générique, renvoyé au client
    """
    if not condition:
        logger.warning("Validation échouée: %s", log_msg)
        raise ValidationError(client_msg)


# --------------------------------------------------------------------------- #
# Sérialisation (exclut les champs sensibles : ici aucun champ privé n'est
# exposé ; la fonction documente le principe et filtre les valeurs None).
# --------------------------------------------------------------------------- #
def serialize_document(obj: Document) -> str:
    """Sérialise un Document en JSON. Exclut les champs None (created_at absent)."""
    data = {k: v for k, v in asdict(obj).items() if v is not None}
    return json.dumps(data, ensure_ascii=False)


def serialize_user(obj: UserPublic) -> str:
    """Sérialise un UserPublic en JSON. (Aucun champ sensible : pas de mot de passe.)"""
    return json.dumps(asdict(obj), ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Désérialisation + validation exhaustive
# --------------------------------------------------------------------------- #
def deserialize_document(raw: str) -> Document:
    """Parse + valide un Document. Rejette tout payload non conforme (fail closed)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON malformé: %s", exc)
        raise ValidationError("Format JSON invalide")

    _require(isinstance(data, dict), f"racine non-objet: {type(data)}")

    # id : entier strictement positif
    doc_id = data.get("id")
    _require(isinstance(doc_id, int) and not isinstance(doc_id, bool),
             f"id type={type(doc_id)}")
    _require(doc_id > 0, f"id non positif: {doc_id}")

    # title : 1-200 chars, non vide après strip
    title = data.get("title")
    _require(isinstance(title, str), f"title type={type(title)}")
    _require(1 <= len(title.strip()) <= 200, f"title longueur={len(title.strip())}")

    # author : 1-100 chars
    author = data.get("author")
    _require(isinstance(author, str), f"author type={type(author)}")
    _require(1 <= len(author.strip()) <= 100, f"author longueur={len(author.strip())}")

    # tags : optionnel, 0-20 éléments, chaque tag str 1-50 chars
    tags = data.get("tags", [])
    _require(isinstance(tags, list), f"tags type={type(tags)}")
    _require(len(tags) <= 20, f"tags trop nombreux: {len(tags)}")
    for t in tags:
        _require(isinstance(t, str), f"tag non-str: {type(t)}")
        _require(1 <= len(t) <= 50, f"tag longueur={len(t)}")

    # classification : optionnel, allowlist
    classification = data.get("classification", "internal")
    _require(classification in CLASSIFICATIONS,
             f"classification hors allowlist: {classification!r}")

    # created_at : optionnel, format ISO 8601 si présent
    created_at = data.get("created_at")
    if created_at is not None:
        _require(isinstance(created_at, str), f"created_at type={type(created_at)}")
        _require(bool(ISO8601_RE.match(created_at)),
                 f"created_at format invalide: {created_at!r}")

    return Document(
        id=doc_id,
        title=title.strip(),
        author=author.strip(),
        tags=list(tags),
        classification=classification,
        created_at=created_at,
    )


def deserialize_user(raw: str) -> UserPublic:
    """Parse + valide un UserPublic. Fail closed."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON malformé: %s", exc)
        raise ValidationError("Format JSON invalide")

    _require(isinstance(data, dict), f"racine non-objet: {type(data)}")

    username = data.get("username")
    _require(isinstance(username, str), f"username type={type(username)}")
    _require(bool(USERNAME_RE.match(username)), f"username invalide: {username!r}")

    display_name = data.get("display_name")
    _require(isinstance(display_name, str), f"display_name type={type(display_name)}")
    _require(1 <= len(display_name) <= 100, f"display_name longueur={len(display_name)}")

    role = data.get("role")
    _require(role in ROLES, f"role hors allowlist: {role!r}")

    return UserPublic(username=username, display_name=display_name, role=role)


# --------------------------------------------------------------------------- #
# Cas de test (2 valides, 3+ invalides)
# --------------------------------------------------------------------------- #
def _run_tests() -> None:
    print("=" * 70)
    print("TP7.1 — Tests de validation du contrat JSON")
    print("=" * 70)

    cases = [
        # (description, payload, doit_etre_valide)
        ("VALIDE — Document complet",
         '{"id": 42, "title": "Rapport Q1", "author": "Alice Dupont", '
         '"tags": ["finance"], "classification": "confidential", '
         '"created_at": "2026-01-15T10:30:00Z"}', True),

        ("VALIDE — Document minimal (defaults appliqués)",
         '{"id": 1, "title": "Note", "author": "Bob"}', True),

        ("INVALIDE — champ obligatoire manquant (author)",
         '{"id": 1, "title": "Sans auteur"}', False),

        ("INVALIDE — type erroné (id en string)",
         '{"id": "42", "title": "X", "author": "A"}', False),

        ("INVALIDE — valeur hors allowlist (classification)",
         '{"id": 1, "title": "X", "author": "A", "classification": "top_secret"}', False),

        ("INVALIDE — id non positif",
         '{"id": 0, "title": "X", "author": "A"}', False),

        ("INVALIDE — JSON malformé",
         '{"id": 1, "title": "X", author: A}', False),
    ]

    passed = 0
    for desc, payload, expect_valid in cases:
        try:
            doc = deserialize_document(payload)
            got_valid = True
            result = f"OK -> {doc}"
        except ValidationError as exc:
            got_valid = False
            result = f"REJET (client voit: '{exc}')"

        status = "PASS" if got_valid == expect_valid else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"\n[{status}] {desc}")
        print(f"        {result}")

    print("\n" + "-" * 70)
    print(f"Résultat : {passed}/{len(cases)} tests conformes aux attentes")

    # Démonstration sérialisation (round-trip)
    print("\n" + "=" * 70)
    print("Démonstration round-trip (serialize -> deserialize)")
    print("=" * 70)
    doc = Document(id=7, title="Plan projet", author="Yassine",
                   tags=["projet", "tp"], classification="internal")
    raw = serialize_document(doc)
    print("Sérialisé :", raw)
    back = deserialize_document(raw)
    print("Désérialisé :", back)
    print("Round-trip identique :", doc == back)

    user = UserPublic(username="alice_d", display_name="Alice Dupont", role="editor")
    print("\nUserPublic sérialisé :", serialize_user(user))


if __name__ == "__main__":
    _run_tests()
