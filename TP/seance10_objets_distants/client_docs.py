"""
TP10 — client_docs.py
======================
Client du DocumentService distant.

Localise l'objet via le name server, crée un proxy, et appelle les méthodes.
Démontre le comportement attendu pour les cas valides ET invalides
(le client ne voit que des messages génériques — cf. TP10.3).

Lancement (après name server + serveur) :
    python3 client_docs.py
"""

from __future__ import annotations

import Pyro5.api
import Pyro5.errors


def run_client() -> None:
    # 1) Localiser le name server, puis l'objet par son nom logique
    ns = Pyro5.api.locate_ns()
    uri = ns.lookup("tp10.documents.service")

    # 2) Créer le proxy et appeler les méthodes distantes
    with Pyro5.api.Proxy(uri) as service:
        print("=" * 60)
        print("Client DocumentService — TP10")
        print("=" * 60)

        # --- Cas nominaux ---
        docs = service.list_documents()
        print("list_documents() ->", docs)

        content = service.get_document_content("doc_001")
        print("get_document_content('doc_001') ->", content)

        # --- Cas d'erreur (le client ne voit qu'un message générique) ---
        test_ids = [
            ("doc_999", "document inexistant"),
            ("../../etc", "tentative path traversal"),
            ("doc;DROP", "tentative injection"),
            ("ab", "trop court"),
        ]
        print("\n-- Cas d'erreur (messages génériques attendus) --")
        for doc_id, label in test_ids:
            try:
                service.get_document_content(doc_id)
                print(f"  {doc_id!r:14} : RÉPONSE INATTENDUE")
            except Exception as exc:
                # Pyro5 propage le type + le message générique du serveur
                print(f"  {doc_id!r:14} ({label}) -> {type(exc).__name__}: {exc}")

        # --- Contrôle d'accès (token) ---
        print("\n-- Contrôle d'accès admin (token) --")
        try:
            print("  bon token   ->", service.admin_reload_index("secret-tp10-2024"))
        except Exception as exc:
            print(f"  bon token   -> {type(exc).__name__}: {exc}")
        try:
            service.admin_reload_index("mauvais")
            print("  mauvais tok -> RÉPONSE INATTENDUE")
        except Exception as exc:
            print(f"  mauvais tok -> {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    try:
        run_client()
    except Pyro5.errors.NamingError:
        print("Erreur : name server introuvable.")
        print("Démarrez d'abord :  python3 -m Pyro5.nameserver")
        print("puis              :  python3 server_docs.py")
