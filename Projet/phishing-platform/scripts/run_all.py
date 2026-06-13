"""
Lance les 4 services de la plateforme dans des processus separes.

Usage : python scripts/run_all.py
Arret : Ctrl+C (arrete proprement tous les services).

Ordre de demarrage : AuthService, AuditService, AnalysisService, puis Gateway.
Chaque service tourne dans son propre processus -> vraie architecture repartie.
"""
from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SERVICES = [
    ("AuthService", [sys.executable, "-m", "auth_service.server"]),
    ("AuditService", [sys.executable, "-m", "audit_service.server"]),
    ("AnalysisService (Pyro5)", [sys.executable, "-m", "analysis_service.server"]),
    ("API Gateway", [sys.executable, "-m", "submission_service.server"]),
]

procs = []


def shutdown(*_):
    print("\nArret des services...")
    for name, proc in procs:
        if proc.poll() is None:
            proc.terminate()
    for name, proc in procs:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("Tous les services sont arretes.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Demarrage de la plateforme distribuee...\n")
    for name, cmd in SERVICES:
        proc = subprocess.Popen(cmd, cwd=str(ROOT))
        procs.append((name, proc))
        print(f"  [OK] {name} (PID {proc.pid})")
        time.sleep(1.5)  # laisse le temps a chaque service de se lier au port

    print("\nPlateforme prete.")
    print("  Gateway   : http://127.0.0.1:8000")
    print("  Lancez le client : python -m client.app  (interface graphique)")
    print("                 ou : python -m client.cli  (console)")
    print("\nCtrl+C pour tout arreter.\n")

    # Surveille les processus : si l'un meurt, on le signale.
    while True:
        time.sleep(2)
        for name, proc in procs:
            if proc.poll() is not None:
                print(f"  [ATTENTION] {name} s'est arrete (code {proc.returncode}).")
                shutdown()


if __name__ == "__main__":
    main()
