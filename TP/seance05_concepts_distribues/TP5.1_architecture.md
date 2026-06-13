# TP5.1 — Schématisation d'architecture distribuée

Projet fil rouge : Système de Gestion Documentaire Distribué (SGDD)

## Objectif

Concevoir l'architecture logique et physique du SGDD en identifiant les
composants, leurs responsabilités et leurs interactions.

## Architecture logique

Le schéma complet est dans le fichier [`architecture_sgdd.svg`](architecture_sgdd.svg).
Résumé textuel :

```
Client → API Gateway → { Auth Service, Stockage Service, Recherche Service }
                              ↓             ↓                    ↓
                         PostgreSQL    MongoDB/S3          Elasticsearch
Stockage → (async) → Recherche (indexation)
Stockage → (async) → Notifications (événement)
```

| Composant | Responsabilité | Technologie type |
|---|---|---|
| API Gateway | Point d'entrée unique, routage, rate limiting, validation JWT | Nginx / Traefik / Python |
| Auth Service | Login, émission de tokens JWT, gestion des rôles | Python (FastAPI), PostgreSQL |
| Stockage Service | CRUD documents, métadonnées | Python, MongoDB / S3 (MinIO) |
| Recherche Service | Indexation et recherche plein texte | Python, Elasticsearch / Whoosh |
| Notifications (optionnel) | Alertes upload / modification | Python, Redis Pub/Sub |

## Architecture physique (déploiement)

| Machine / conteneur | Composants co-localisés | Justification |
|---|---|---|
| Nœud edge | API Gateway | Exposé, isolé du reste |
| Nœud applicatif 1 | Auth Service + sa base | Donnée sensible isolée |
| Nœud applicatif 2 | Stockage Service | Charge I/O dédiée |
| Nœud applicatif 3 | Recherche Service + index | Ressources CPU/mémoire dédiées |

## Réponses aux questions du gabarit

- **Combien de services ?** 4 cœurs (Gateway, Auth, Stockage, Recherche) +
  1 optionnel (Notifications). Frontières = responsabilité métier unique par service.
- **Protocoles entre services ?** REST/HTTP synchrone pour les requêtes
  client (Gateway → services) ; messages asynchrones (Pub/Sub) pour
  l'indexation et les notifications (découplage temporel).
- **Bases de données ?** Une par service (database-per-service) pour
  l'isolation et l'autonomie de déploiement.
- **Appels parallèles possibles ?** À l'upload, l'indexation et la
  notification se font en parallèle, hors du chemin critique de la réponse.
- **Chemin critique ?** Upload : Client → Gateway → Auth → Stockage (la
  réponse est renvoyée dès la sauvegarde ; indexation/notification suivent en async).

## Description justificative

L'architecture sépare les responsabilités en services autonomes derrière une
API Gateway unique, qui centralise l'authentification et le rate limiting.
Chaque service possède sa propre base pour rester déployable indépendamment.
Les opérations non critiques (indexation, notification) sont sorties du chemin
critique via des messages asynchrones : l'utilisateur reçoit sa réponse dès que
le document est sauvegardé, sans attendre l'indexation. Ce choix privilégie la
réactivité perçue tout en acceptant une cohérence éventuelle sur la recherche.

## Piège classique évité

L'architecture **logique** (services + interactions) est distincte de
l'architecture **physique** (machines/conteneurs). Deux services logiques
peuvent tourner sur la même machine en dev mais sur des machines séparées en prod.
