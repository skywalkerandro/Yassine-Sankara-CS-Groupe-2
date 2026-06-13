"""
TP7.3 — Protocol Buffers en Python (schéma + échange)
======================================================
Sérialiser/désérialiser un Document avec Protobuf, tester la compatibilité
arrière, et comparer la taille du payload avec JSON.

Pré-requis :
    pip install protobuf
    protoc --python_out=. document.proto   (génère document_pb2.py)

Exécution :
    python3 tp7_3_protobuf.py
"""

from __future__ import annotations

import json

import document_pb2  # généré par protoc à partir de document.proto


def build_document() -> document_pb2.Document:
    """Construit un Document Protobuf de référence."""
    doc = document_pb2.Document()
    doc.id = 42
    doc.title = "Rapport Q1"
    doc.author = "Alice Dupont"
    doc.tags.extend(["finance", "2026"])
    doc.classification = "confidential"
    return doc


def equivalent_json(doc: document_pb2.Document) -> str:
    """Même donnée, sérialisée en JSON, pour comparaison de taille."""
    payload = {
        "id": doc.id,
        "title": doc.title,
        "author": doc.author,
        "tags": list(doc.tags),
        "classification": doc.classification,
    }
    return json.dumps(payload, ensure_ascii=False)


def demo_encode_decode() -> None:
    print("=" * 70)
    print("TP7.3 — Protobuf : encode / decode")
    print("=" * 70)

    doc = build_document()

    # Encodage binaire
    wire = doc.SerializeToString()
    print("Encodé (binaire, repr) :", wire)

    # Décodage
    decoded = document_pb2.Document()
    decoded.ParseFromString(wire)
    print("Décodé :")
    print(f"  id={decoded.id} title={decoded.title!r} author={decoded.author!r}")
    print(f"  tags={list(decoded.tags)} classification={decoded.classification!r}")

    assert decoded.id == doc.id and list(decoded.tags) == list(doc.tags)
    print("Round-trip Protobuf : OK")


def demo_backward_compat() -> None:
    """Un message avec le champ 'priority' (champ 6) lu par le même schéma :
    si on simule un lecteur ancien, le champ inconnu est simplement ignoré.
    Ici on démontre l'inverse : ajouter priority ne casse pas le décodage."""
    print("\n" + "=" * 70)
    print("Compatibilité arrière (ajout du champ priority = 6)")
    print("=" * 70)

    doc = build_document()
    doc.priority = "urgent"           # champ ajouté
    wire = doc.SerializeToString()

    # Décodage avec le schéma courant : le champ est lu normalement.
    decoded = document_pb2.Document()
    decoded.ParseFromString(wire)
    print(f"priority décodé : {decoded.priority!r}")
    print(
        "Note : un binaire généré AVANT l'ajout de 'priority' reste décodable\n"
        "(champ absent -> valeur par défaut ''), et un lecteur ANCIEN ignore\n"
        "silencieusement le champ 6 qu'il ne connaît pas. C'est la rétro/\n"
        "forward-compatibilité native de Protobuf."
    )


def demo_size_comparison() -> None:
    print("\n" + "=" * 70)
    print("Comparaison de taille JSON vs Protobuf (mêmes données)")
    print("=" * 70)

    doc = build_document()
    pb_bytes = len(doc.SerializeToString())
    json_str = equivalent_json(doc)
    json_bytes = len(json_str.encode("utf-8"))

    print(f"JSON     : {json_bytes:>3} octets  -> {json_str}")
    print(f"Protobuf : {pb_bytes:>3} octets")
    ratio = json_bytes / pb_bytes if pb_bytes else float("inf")
    print(f"Ratio    : Protobuf est ~{ratio:.2f}x plus compact que JSON")

    print("\n" + "-" * 70)
    print("Tableau comparatif")
    print("-" * 70)
    rows = [
        ("Taille payload (octets)", str(json_bytes), str(pb_bytes),
         f"ratio {ratio:.2f}x"),
        ("Lisibilité", "Humaine (texte)", "Binaire opaque", "JSON gagne"),
        ("Validation de types", "Applicative", "Schéma .proto", "Protobuf gagne"),
        ("Compatibilité ajout champ", "Manuelle", "Native (n° champ)", "Protobuf gagne"),
        ("Tooling nécessaire", "Aucun (stdlib)", "protoc + lib", "JSON gagne"),
    ]
    print(f"{'Critère':<28}{'JSON':<18}{'Protobuf':<20}{'Commentaire'}")
    for crit, j, p, c in rows:
        print(f"{crit:<28}{j:<18}{p:<20}{c}")


if __name__ == "__main__":
    demo_encode_decode()
    demo_backward_compat()
    demo_size_comparison()
