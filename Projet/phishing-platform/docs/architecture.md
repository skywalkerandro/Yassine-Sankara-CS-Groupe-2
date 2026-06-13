# Schema d'architecture

## Vue d'ensemble

La plateforme suit une architecture **repartie en microservices**. Chaque
composant tourne dans son propre processus et expose une responsabilite unique.
Le client ne communique qu'avec l'**API Gateway**, qui orchestre les autres
services. C'est le principe du **point d'entree unique**.

```
                          +---------------------------+
                          |   CLIENT (appli native)   |
                          |   PySide6  /  console CLI  |
                          +-------------+-------------+
                                        |
                                        |  HTTP / JSON
                                        |  (Authorization: Bearer <token>)
                                        v
                          +---------------------------+
                          |       API GATEWAY         |
                          |   (SubmissionService)     |
                          |  - valide les entrees     |
                          |  - orchestre les services |
                          |  - controle les roles     |
                          +----+-----------+-----+----+
                               |           |     |
              HTTP/JSON        |           |     |        HTTP/JSON
        +----------------------+           |     +---------------------+
        |                                  |                           |
        v                          RPC Pyro5 (objet distant)          v
+----------------+                         |                  +----------------+
|  AuthService   |                         v                  |  AuditService  |
|  HTTP / JSON   |                +------------------+        |  HTTP / JSON   |
|  - login       |                | AnalysisService  |        |  - record      |
|  - verify      |                |   (Pyro5 / RPC)  |        |  - list (admin)|
|  - logout      |                |  - analyze_email |        +-------+--------+
|  - roles       |                |  - moteur de     |                |
+-------+--------+                |    scoring       |                |
        |                         +------------------+                |
        |                                                             |
        +------------------------------+------------------------------+
                                       |
                                       v
                          +---------------------------+
                          |   STOCKAGE LOCAL (SQLite) |
                          |  users / sessions /       |
                          |  reports / audit_events   |
                          +---------------------------+
```

## Protocoles de communication

| De            | Vers            | Protocole      | Format  |
|---------------|-----------------|----------------|---------|
| Client        | API Gateway     | HTTP           | JSON    |
| API Gateway   | AuthService     | HTTP           | JSON    |
| API Gateway   | AnalysisService | **RPC Pyro5**  | serpent |
| API Gateway   | AuditService    | HTTP           | JSON    |
| Tous          | SQLite          | sqlite3 (local)| -       |

L'exigence "au moins un mecanisme RPC ou objet distant" est satisfaite par
**AnalysisService**, expose via **Pyro5** : la Gateway obtient un proxy de
l'objet distant et appelle `analyze_email(...)` comme une methode locale.

## Ports (par defaut, configurables via variables d'environnement)

| Service          | Hote      | Port |
|------------------|-----------|------|
| API Gateway      | 127.0.0.1 | 8000 |
| AuthService      | 127.0.0.1 | 8001 |
| AuditService     | 127.0.0.1 | 8002 |
| AnalysisService  | 127.0.0.1 | 8003 |

## Flux d'une soumission (cas nominal)

1. Le client envoie `POST /submit` a la Gateway avec son token.
2. La Gateway appelle `AuthService /verify` pour valider le token et le role.
3. La Gateway valide et nettoie les entrees (defense en profondeur).
4. La Gateway appelle `AnalysisService.analyze_email(...)` **en RPC Pyro5**.
5. La Gateway enregistre le signalement dans SQLite (table `reports`).
6. La Gateway appelle `AuditService /record` pour tracer l'evenement.
7. La Gateway renvoie au client le score, le niveau et la justification.

## Resilience

- Tout appel distant a un **timeout** (5 s par defaut).
- Si AnalysisService est injoignable -> la Gateway renvoie une erreur 503
  propre, et l'echec est trace dans l'audit.
- Si AuditService est injoignable -> l'operation metier n'echoue pas (l'audit
  est best-effort), mais l'indisponibilite est journalisee localement.
