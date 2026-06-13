"""
Client console (alternative legere a l'appli graphique).

Utile pour les tests rapides et pour demontrer la plateforme sans interface
graphique. Communique avec la Gateway via la meme couche ApiClient.

Lancement : python -m client.cli
"""
from __future__ import annotations

import getpass
import sys

from client.api import ApiClient, ApiError

LEVEL_LABELS = {"faible": "FAIBLE", "moyen": "MOYEN", "eleve": "ELEVE"}


def prompt(msg: str) -> str:
    try:
        return input(msg)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def do_login(api: ApiClient) -> bool:
    print("=== Connexion ===")
    login = prompt("Identifiant : ").strip()
    password = getpass.getpass("Mot de passe : ")
    try:
        api.connect(login, password)
        print(f"Connecte en tant que {api.login} ({api.role}).\n")
        return True
    except ApiError as exc:
        print(f"Echec : {exc}\n")
        return False


def do_submit(api: ApiClient):
    print("\n--- Nouveau signalement ---")
    sender = prompt("Expediteur : ").strip()
    subject = prompt("Objet : ").strip()
    print("Contenu (terminez par une ligne vide) :")
    lines = []
    while True:
        line = prompt("")
        if line == "":
            break
        lines.append(line)
    body = "\n".join(lines)
    attach = prompt("Piece jointe ? (o/N) : ").strip().lower() == "o"
    try:
        r = api.submit(sender, subject, body, [], attach)
    except ApiError as exc:
        print(f"Erreur : {exc}")
        return
    print(f"\n  Signalement #{r['id']}")
    print(f"  Niveau de risque : {LEVEL_LABELS.get(r['level'], r['level'])}  (score {r['score']}/100)")
    print("  Justification :")
    for reason in r["reasons"]:
        print(f"    - {reason}")
    print()


def do_list(api: ApiClient):
    try:
        reports = api.list_reports()
    except ApiError as exc:
        print(f"Erreur : {exc}")
        return
    print(f"\n--- {len(reports)} signalement(s) ---")
    for r in reports:
        print(f"  #{r['id']:<3} [{r['risk_level']:<6}] {r['sender']:<35} {r.get('subject','')}")
    print()


def do_search(api: ApiClient):
    sender = prompt("Expediteur (vide=tous) : ").strip()
    level = prompt("Niveau faible/moyen/eleve (vide=tous) : ").strip()
    keyword = prompt("Mot-cle (vide=aucun) : ").strip()
    try:
        results = api.search_reports(sender, level, keyword)
    except ApiError as exc:
        print(f"Erreur : {exc}")
        return
    print(f"\n--- {len(results)} resultat(s) ---")
    for r in results:
        print(f"  #{r['id']:<3} [{r['risk_level']:<6}] {r['sender']}")
    print()


def do_audit(api: ApiClient):
    try:
        events = api.list_audit()
    except ApiError as exc:
        print(f"Erreur : {exc}")
        return
    print(f"\n--- Journal d'audit ({len(events)} evenements) ---")
    for e in events:
        print(f"  [{e['outcome']:<8}] {e.get('actor',''):<12} {e['action']:<10} {e.get('details','')}")
    print()


def menu(api: ApiClient):
    options = [
        ("Soumettre un e-mail suspect", do_submit),
        ("Lister les signalements", do_list),
        ("Rechercher", do_search),
    ]
    if api.is_admin():
        options.append(("Journal d'audit", do_audit))
    while True:
        print("=" * 40)
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i}. {label}")
        print("  0. Quitter")
        choice = prompt("> ").strip()
        if choice == "0":
            print("Au revoir.")
            return
        try:
            idx = int(choice) - 1
            options[idx][1](api)
        except (ValueError, IndexError):
            print("Choix invalide.\n")


def main():
    api = ApiClient()
    print("Plateforme anti-phishing - client console\n")
    while not do_login(api):
        pass
    menu(api)


if __name__ == "__main__":
    main()
