# Applications Réparties et Cybersécurité

Dépôt regroupant les travaux pratiques (TP guidés) et le projet du module
*Applications Réparties et Cybersécurité*.

## Auteur

**Sankara Kabem Yassine**

---

## Contenu du dépôt

| Dossier | Description |
|---|---|
| [`TP/`](TP/) | Les quatre TP guidés (séances 5, 6, 7 et 10), partageant un même projet fil rouge : un Système de Gestion Documentaire Distribué |
| [`Projet/`](Projet/) | Le projet `phishing-platform` — plateforme distribuée de détection et qualification d'e-mails de phishing (voir le [README du projet](Projet/README.md) pour le détail) |

---

## 📂 Travaux pratiques

Les TP construisent et sécurisent progressivement un **système documentaire distribué** :

| Séance | Sujet | Nature |
|---|---|---|
| 5 | Concepts des systèmes distribués | Conceptuel (architecture, sécurité) |
| 6 | Communication, APIs et fiabilité | Conceptuel (contrat d'API, résilience) |
| 7 | Sérialisation et marshalling | Code (JSON, versioning, Protobuf) |
| 10 | Invocation d'objets distants | Code (Pyro5, serveur/client) |

Chaque séance possède son propre `README.md` détaillé dans son dossier. Voir
[`TP/README.md`](TP/README.md) pour le sommaire complet et les instructions
d'exécution du code.

---

## 🚀 Projet — Phishing Platform

Mini plateforme distribuée permettant de **signaler, analyser et qualifier** des e-mails suspects.
Développée en Python, elle repose sur 4 services indépendants qui communiquent réellement entre eux.

**Points clés :**
- Architecture microservices (API Gateway, AuthService, AnalysisService en RPC Pyro5, AuditService)
- Moteur de scoring heuristique avec justification lisible (faible / moyen / élevé)
- Authentification avec rôles (analyste / administrateur)
- Interface graphique native (PySide6) compilable en `.app` macOS ou `.exe` Windows
- Sécurité by design : hachage des mots de passe, validation stricte, rate limiting, audit

→ Voir [`Projet/README.md`](Projet/README.md) pour l'installation et le lancement complets.

---

## 🛠️ Technologies utilisées

- **Python 3.10+** (bibliothèque standard : `json`, `dataclasses`, `re`, `logging`, `http.server`, `sqlite3`)
- **Protocol Buffers** (`protobuf` + `protoc`) — TP séance 7
- **Pyro5** — objets distants (TP séance 10 + projet)
- **PySide6** — interface graphique native (projet)
- **PyInstaller** — compilation en application native (projet)
- **SQLite** — stockage local (projet)

---

## ⚡ Exécution rapide du code des TP

```bash
# Séance 7 — Sérialisation
cd TP/seance07_serialisation
pip install protobuf
protoc --python_out=. document.proto
python3 tp7_1_contrat_json.py

# Séance 10 — Objets distants
cd ../seance10_objets_distants
pip install Pyro5
python3 run_demo.py
```

---

## ⚡ Lancement rapide du projet

```bash
cd Projet/phishing-platform
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py --reset

# Terminal 1 — démarrer les services
python scripts/run_all.py

# Terminal 2 — lancer le client
python -m client.app
```

Comptes de démo : `analyste` / `Analyste2024` — `admin` / `Admin2024`
