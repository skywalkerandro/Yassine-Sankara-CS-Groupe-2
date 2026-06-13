# TP6.1 — Spécification d'API (contrat)

Projet fil rouge : Système de Gestion Documentaire Distribué

## Objectif

Définir le contrat d'API complet pour chaque service : méthode HTTP, payload
d'entrée/sortie, codes d'erreur, idempotence, mesures de sécurité. URLs
versionnées (`/api/v1/…`).

## Contrat d'API

| Endpoint | Méthode | Entrée (JSON) | Sortie (JSON) | Erreurs | Idempotent ? | Sécurité |
|---|---|---|---|---|---|---|
| `/api/v1/auth/login` | POST | `{username, password}` | `{token, expires_at}` | 400, 401, 429 | Non (génère un token) | Rate limiting, TLS, pas de distinction « user inexistant » / « mauvais mdp » |
| `/api/v1/auth/verify` | GET | Header `Authorization: Bearer <token>` | `{valid, user_id, roles}` | 401 | Oui | Usage inter-service |
| `/api/v1/documents` | POST | `{title, content, tags}` | `{id, title, created_at}` | 400, 401, 403, 413 | Non → `Idempotency-Key` | AuthN + AuthZ (éditeur+), validation, taille max |
| `/api/v1/documents` | GET | Query: `page, per_page, sort, order, tag` | `{data[], total, page, per_page}` | 400, 401 | Oui | AuthN, pagination forcée (max 100) |
| `/api/v1/documents/{id}` | GET | Path: `id` (UUID) | `{id, title, content, …}` | 401, 403, 404 | Oui | AuthN + AuthZ (propriétaire ou lecteur) |
| `/api/v1/documents/{id}` | PUT | `{title, content, tags}` | `{id, title, updated_at}` | 400, 401, 403, 404, 409 | Oui | AuthN + AuthZ (propriétaire ou éditeur) |
| `/api/v1/documents/{id}` | DELETE | Path: `id` (UUID) | `204 No Content` | 401, 403, 404 | Oui | AuthN + AuthZ (propriétaire ou admin), audit log |
| `/api/v1/search` | GET | Query: `q, page, per_page, tag, date_from, date_to` | `{results[], total, page}` | 400, 401, 429 | Oui | AuthN, rate limiting, résultats filtrés par AuthZ |

## Codes HTTP essentiels

| Code | Signification | Usage |
|---|---|---|
| 200 / 201 / 204 | OK / Créé / Pas de contenu | Succès |
| 400 | Bad Request | Validation d'entrée échouée |
| 401 | Unauthorized | Authentification manquante/invalide |
| 403 | Forbidden | Authentifié mais pas autorisé |
| 404 | Not Found | Ressource inexistante |
| 409 | Conflict | Conflit de version (édition concurrente) |
| 413 | Payload Too Large | Document trop volumineux |
| 429 | Too Many Requests | Rate limiting déclenché |

## Idempotence

Un endpoint est idempotent si l'appeler N fois produit le même effet qu'une
seule fois. Les lectures (GET) et `PUT`/`DELETE` le sont naturellement. Le
`POST` de création ne l'est pas → on fournit une **Idempotency-Key** (UUID
généré côté client) pour rendre les retries sûrs.

## Piège classique : énumération d'IDs

Des IDs séquentiels (`1, 2, 3…`) permettent à un attaquant de deviner les
ressources existantes. **Utiliser des UUID v4** (aléatoires, non prédictibles)
pour les identifiants de documents.
