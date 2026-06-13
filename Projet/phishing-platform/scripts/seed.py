"""
Initialise la base et cree les comptes de demonstration.
A executer une fois avant la premiere utilisation.

Comptes crees :
- admin   / Admin#2024     (role administrateur)
- analyste / Analyste#2024  (role analyste)

Les mots de passe sont haches avant stockage (jamais en clair).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permet d'executer le script directement (ajoute la racine au PYTHONPATH).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import config
from common.database import init_db, reset_db
from auth_service import repository as auth_repo


DEMO_USERS = [
    ("admin", "Admin#2024", config.ROLE_ADMIN),
    ("analyste", "Analyste#2024", config.ROLE_ANALYST),
]


def main(reset: bool = False):
    if reset:
        reset_db()
        print("Base reinitialisee.")
    else:
        init_db()

    for login, password, role in DEMO_USERS:
        if auth_repo.user_exists(login):
            print(f"  - utilisateur '{login}' existe deja, ignore")
            continue
        auth_repo.create_user(login, password, role)
        print(f"  - utilisateur '{login}' cree (role: {role})")

    print("\nComptes de demonstration :")
    for login, password, role in DEMO_USERS:
        print(f"    login: {login:10s} | mot de passe: {password:16s} | role: {role}")


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
