"""
Test de bout en bout AUTONOME.

Demarre les 4 services dans des sous-processus, attend qu'ils ecoutent,
deroule un scenario complet, puis arrete tout proprement. Conçu pour tourner
en une seule invocation (pas de processus laisses en arriere-plan).

Usage : python scripts/e2e_test.py
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from common import config  # noqa: E402
from common.http_client import post_json, HttpStatusError  # noqa: E402

SERVICES = [
    ("auth", [sys.executable, "-m", "auth_service.server"]),
    ("audit", [sys.executable, "-m", "audit_service.server"]),
    ("analysis", [sys.executable, "-m", "analysis_service.server"]),
    ("gateway", [sys.executable, "-m", "submission_service.server"]),
]
PORTS = {"auth": 8001, "audit": 8002, "analysis": 8003, "gateway": 8000}


def wait_port(port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            time.sleep(0.2)
        finally:
            try:
                s.close()
            except OSError:
                pass
    return False


def check(label: str, condition: bool):
    status = "OK  " if condition else "ECHEC"
    print(f"   [{status}] {label}")
    if not condition:
        raise AssertionError(label)


def run_scenario() -> bool:
    gw = config.GATEWAY_URL
    print("\n--- SCENARIO ---")

    # 1. Refus non authentifie
    try:
        post_json(f"{gw}/submit", {"sender": "x@y.com"}, timeout=5)
        check("Refus d'acces non authentifie", False)
    except HttpStatusError as e:
        check(f"Refus d'acces non authentifie (HTTP {e.status})", e.status == 403)

    # 2. Mauvais mot de passe
    try:
        post_json(f"{gw}/login", {"login": "admin", "password": "X"}, timeout=5)
        check("Rejet mauvais mot de passe", False)
    except HttpStatusError as e:
        check(f"Rejet mauvais mot de passe (HTTP {e.status})", e.status == 401)

    # 3. Connexion analyste
    resp = post_json(f"{gw}/login", {"login": "analyste", "password": "Analyste#2024"}, timeout=5)
    check("Connexion analyste", resp.get("role") == "analyst" and "token" in resp)
    auth_h = {"Authorization": f"Bearer {resp['token']}"}

    # 4. Soumission phishing
    r = post_json(f"{gw}/submit", {
        "sender": "securite@paypa1.tk",
        "subject": "URGENT verifiez votre compte",
        "body": "Compte bloque. Confirmez votre mot de passe : http://bit.ly/x",
        "urls": ["http://bit.ly/x"],
    }, headers=auth_h, timeout=5)
    check(f"Soumission phishing -> niveau '{r['level']}' (score {r['score']})", r["level"] == "eleve")

    # 5. Soumission legitime
    r2 = post_json(f"{gw}/submit", {
        "sender": "rh@mon-entreprise.com", "subject": "Planning",
        "body": "Bonjour, voici le planning. Bonne journee.", "urls": [],
    }, headers=auth_h, timeout=5)
    check(f"Soumission legitime -> niveau '{r2['level']}' (score {r2['score']})", r2["level"] == "faible")

    # 6. Liste
    resp = post_json(f"{gw}/reports/list", {}, headers=auth_h, timeout=5)
    check(f"Liste des signalements ({len(resp['reports'])})", len(resp["reports"]) >= 2)

    # 7. Recherche
    resp = post_json(f"{gw}/reports/search", {"level": "eleve"}, headers=auth_h, timeout=5)
    check(f"Recherche niveau eleve ({len(resp['reports'])})", len(resp["reports"]) >= 1)

    # 8. Audit refuse a l'analyste
    try:
        post_json(f"{gw}/audit/list", {}, headers=auth_h, timeout=5)
        check("Audit refuse a l'analyste", False)
    except HttpStatusError as e:
        check(f"Audit refuse a l'analyste (HTTP {e.status})", e.status == 403)

    # 9. Admin accede a l'audit
    admin = post_json(f"{gw}/login", {"login": "admin", "password": "Admin#2024"}, timeout=5)
    admin_h = {"Authorization": f"Bearer {admin['token']}"}
    resp = post_json(f"{gw}/audit/list", {"limit": 10}, headers=admin_h, timeout=5)
    check(f"Admin consulte l'audit ({len(resp['events'])} evenements)", len(resp["events"]) >= 1)

    # 10. Health check (resilience)
    resp = post_json(f"{gw}/login", {"login": "admin", "password": "Admin#2024"}, timeout=5)
    health = __import__("urllib.request", fromlist=["urlopen"])
    import urllib.request, json
    with urllib.request.urlopen(f"{gw}/health", timeout=5) as h:
        hdata = json.loads(h.read())
    check(f"Health: analysis={hdata['analysis_service']}, auth={hdata['auth_service']}",
          hdata["analysis_service"] == "ok")

    return True


def main():
    # Re-seed propre.
    from common.database import reset_db
    from auth_service import repository as ar
    reset_db()
    ar.create_user("admin", "Admin#2024", config.ROLE_ADMIN)
    ar.create_user("analyste", "Analyste#2024", config.ROLE_ANALYST)
    print("Base reinitialisee + comptes crees.")

    procs = []
    try:
        print("Demarrage des services...")
        for name, cmd in SERVICES:
            log = open(f"/tmp/e2e_{name}.log", "w")
            p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL)
            procs.append((name, p, log))
            if not wait_port(PORTS[name], timeout=12):
                raise RuntimeError(f"Le service '{name}' n'ecoute pas sur le port {PORTS[name]}")
            print(f"   [OK] {name} ecoute sur {PORTS[name]}")

        ok = run_scenario()
        print("\n" + "=" * 50)
        print("RESULTAT : TOUS LES TESTS SONT PASSES" if ok else "RESULTAT : ECHEC")
        print("=" * 50)
        return 0 if ok else 1
    except Exception as exc:
        print(f"\nERREUR : {type(exc).__name__}: {exc}")
        for name, p, log in procs:
            log.flush()
            print(f"\n--- log {name} ---")
            try:
                print(Path(f"/tmp/e2e_{name}.log").read_text()[:800])
            except OSError:
                pass
        return 1
    finally:
        for name, p, log in procs:
            if p.poll() is None:
                p.terminate()
        for name, p, log in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
            log.close()
        print("\nServices arretes.")


if __name__ == "__main__":
    sys.exit(main())
