"""
Script de demonstration automatique.

Charge le jeu de donnees demo_data/emails_demo.json, se connecte en tant
qu'analyste, soumet chaque e-mail et affiche le score obtenu vs le niveau
attendu. Sert de demonstration reproductible (section "Demonstration attendue").

Pre-requis : les services doivent tourner (python scripts/run_all.py).
Usage : python scripts/demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from client.api import ApiClient, ApiError

DEMO_FILE = ROOT / "demo_data" / "emails_demo.json"


def main():
    api = ApiClient()
    print("Connexion en tant qu'analyste...")
    try:
        api.connect("analyste", "Analyste#2024")
    except ApiError as exc:
        print(f"Impossible de se connecter : {exc}")
        print("Les services sont-ils demarres ? (python scripts/run_all.py)")
        return 1

    emails = json.loads(DEMO_FILE.read_text(encoding="utf-8"))
    print(f"Soumission de {len(emails)} e-mails de demonstration :\n")

    ok = 0
    for i, mail in enumerate(emails, 1):
        attendu = mail.get("_attendu", "?")
        try:
            r = api.submit(
                mail["sender"], mail.get("subject", ""), mail.get("body", ""),
                [], mail.get("has_attachment", False),
            )
        except ApiError as exc:
            print(f"  {i}. ERREUR : {exc}")
            continue
        match = "OK" if r["level"] == attendu else "differe"
        if r["level"] == attendu:
            ok += 1
        print(f"  {i}. {mail['sender'][:38]:<38}")
        print(f"     attendu={attendu:<7} obtenu={r['level']:<7} score={r['score']:<3} [{match}]")

    print(f"\nResultat : {ok}/{len(emails)} correspondent au niveau attendu.")
    print("(Note : le niveau exact depend du barème ; l'essentiel est la coherence.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
