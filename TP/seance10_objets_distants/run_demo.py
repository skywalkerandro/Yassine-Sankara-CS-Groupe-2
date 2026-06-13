"""
run_demo.py — Orchestrateur de démonstration (TP10)
====================================================
Lance automatiquement, dans l'ordre :
    1) le name server Pyro5
    2) le serveur DocumentService
    3) le client

Sert à vérifier l'ensemble en une commande, et à capturer la sortie pour
le rapport. En usage réel, on lance les 3 dans 3 terminaux séparés.

    python3 run_demo.py
"""

import subprocess
import sys
import time
import os
import signal

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    env = dict(os.environ)
    procs = []
    try:
        # 1) Name server
        print(">> Démarrage du name server...")
        ns = subprocess.Popen(
            [sys.executable, "-m", "Pyro5.nameserver"],
            cwd=HERE, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(ns)
        time.sleep(2.5)

        # 2) Serveur
        print(">> Démarrage du serveur DocumentService...")
        srv = subprocess.Popen(
            [sys.executable, "server_docs.py"],
            cwd=HERE, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(srv)
        time.sleep(2.5)

        # 3) Client (on capture sa sortie)
        print(">> Exécution du client...\n")
        result = subprocess.run(
            [sys.executable, "client_docs.py"],
            cwd=HERE, env=env,
            capture_output=True, text=True, timeout=30,
        )
        print(result.stdout)
        if result.returncode != 0:
            print("STDERR:", result.stderr)
        return result.returncode
    finally:
        # Nettoyage : terminer serveur puis name server
        for p in reversed(procs):
            try:
                p.send_signal(signal.SIGTERM)
                p.wait(timeout=5)
            except Exception:
                p.kill()


if __name__ == "__main__":
    sys.exit(main())
