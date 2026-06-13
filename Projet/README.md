# 🔍 Phishing Platform

> Plateforme distribuée de détection et qualification d'e-mails de phishing  
> Projet de fin de semestre — Module *Applications réparties et cybersécurité*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![Pyro5](https://img.shields.io/badge/RPC-Pyro5-orange)
![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 📋 Description

Une mini plateforme distribuée permettant à une organisation de **centraliser, analyser et qualifier** les e-mails suspects signalés par ses employés.

L'utilisateur soumet un e-mail → la plateforme l'analyse via plusieurs services qui communiquent entre eux → elle renvoie un **score de risque** (faible / moyen / élevé) avec une **justification lisible**.

---

## 🏗️ Architecture

```
Client (PySide6 / CLI)
        │  HTTP/JSON + Bearer token
        ▼
   API Gateway ──HTTP/JSON──▶ AuthService     (login, tokens, rôles)
        │       ──RPC Pyro5──▶ AnalysisService (scoring heuristique)
        │       ──HTTP/JSON──▶ AuditService    (journal d'audit)
        ▼
   SQLite  (users · sessions · reports · audit_events)
```

| Service | Rôle | Port |
|---|---|---|
| API Gateway | Point d'entrée, orchestration | 8000 |
| AuthService | Authentification, tokens, rôles | 8001 |
| AuditService | Journal d'audit | 8002 |
| AnalysisService | Moteur de scoring **(RPC Pyro5)** | 8003 |

---

## ⚙️ Installation

> Prérequis : **Python 3.10+**

```bash
# 1. Cloner le dépôt
git clone https://github.com/<ton-username>/phishing-platform.git
cd phishing-platform

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Initialiser la base et créer les comptes de démo
python scripts/seed.py --reset
```

---

## 🚀 Lancement

### Terminal 1 — démarrer les services

```bash
source .venv/bin/activate
python scripts/run_all.py
```

Laisse ce terminal ouvert. Les 4 services démarrent automatiquement.

### Terminal 2 — lancer le client

```bash
source .venv/bin/activate

# Interface graphique native (PySide6)
python -m client.app

# OU client console
python -m client.cli
```

### Comptes de démonstration

| Login | Mot de passe | Rôle |
|---|---|---|
| `analyste` | `Analyste2024` | Analyste (soumettre, consulter) |
| `admin` | `Admin2024` | Admin (+ accès journal d'audit) |

---

## 🖥️ Application native (.app / .exe)

Le client peut être compilé en application autonome :

```bash
source .venv/bin/activate
python scripts/build_app.py
```

- **macOS** → `dist/PhishingClient.app`
- **Windows** → `dist/PhishingClient.exe`

> ⚠️ PyInstaller ne fait pas de compilation croisée. Pour le `.exe` Windows, relance ce script sur une machine Windows.

> **macOS :** lors de la première ouverture, faire **clic droit → Ouvrir** car l'appli n'est pas signée Apple.

---

## 🧪 Tests

```bash
# Tests unitaires (moteur d'analyse)
python tests/test_engine.py

# Tests unitaires (sécurité)
python tests/test_security.py

# Test de bout en bout (démarre tout, scénario complet, arrête tout)
python scripts/e2e_test.py

# Démonstration automatique sur le jeu de données
python scripts/demo.py
```

---

## 🔒 Sécurité

| Menace | Contre-mesure |
|---|---|
| Mots de passe en clair | Hachage PBKDF2-HMAC-SHA256 + sel aléatoire |
| Vol de tokens | Hash du token stocké, jamais le token brut |
| Injection SQL | Requêtes paramétrées uniquement |
| Entrées malveillantes | Validation + nettoyage côté serveur |
| Flood / abus | Rate limiting par IP (fenêtre glissante) |
| Désérialisation | Pyro5/serpent (pas de pickle), JSON pour HTTP |
| Élévation de privilèges | Contrôle de rôle sur chaque route |
| Fuite d'information | Messages d'erreur génériques côté client |

Détail complet → [`docs/menaces.md`](docs/menaces.md)

---

## 📁 Structure du projet

```
phishing-platform/
├── common/               # Config, sécurité, validation, BDD, logs
├── auth_service/         # AuthService (HTTP/JSON)
├── submission_service/   # API Gateway
├── analysis_service/     # AnalysisService (Pyro5 RPC) + moteur scoring
├── audit_service/        # AuditService (HTTP/JSON)
├── client/               # App PySide6 + CLI
├── scripts/              # seed, run_all, demo, e2e_test, build_app
├── tests/                # Tests unitaires
├── demo_data/            # E-mails de démonstration (6 cas)
├── docs/                 # Architecture, rapport, tableau des menaces
├── icon.png              # Icône de l'application
├── requirements.txt
└── README.md
```

---

## 📄 Livrables

- [Architecture](docs/architecture.md) — schéma et flux détaillés
- [Rapport](docs/rapport.md) — rapport synthétique (~1800 mots)
- [Tableau des menaces](docs/menaces.md) — analyse et contre-mesures

---

## 🛠️ Stack technique

- **Python 3.10+** — langage unique (exigence du projet)
- **PySide6** — interface graphique native
- **Pyro5** — RPC / objet distant (AnalysisService)
- **SQLite** — stockage local (aucun serveur requis)
- **http.server** — serveurs HTTP (librairie standard)
- **PyInstaller** — compilation en appli native
