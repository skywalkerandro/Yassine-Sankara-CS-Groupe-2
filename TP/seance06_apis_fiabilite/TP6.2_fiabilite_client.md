# TP6.2 — Fiabilité côté client (scénarios de panne)

Projet fil rouge : Système de Gestion Documentaire Distribué

## Objectif

Définir les politiques de fiabilité du client (timeout, retry, backoff,
idempotence) et analyser trois scénarios de panne.

## Politiques recommandées par service

| Service | Timeout | Max retries | Base delay | Codes retryables | Idempotency key ? |
|---|---|---|---|---|---|
| Auth (login) | 5 s | 1 | 1 s | 502, 503, 504 | Non |
| Auth (verify) | 3 s | 2 | 0.5 s | 502, 503, 504 | Non (GET) |
| Documents (GET) | 10 s | 2 | 1 s | 500, 502, 503, 504 | Non (lecture) |
| Documents (POST) | 15 s | **0** (pas de retry auto) | — | — | Oui (UUID client) |
| Search (query) | 8 s | 2 | 1 s | 502, 503 | Non (lecture) |

## Analyse des trois scénarios

| Scénario | Risque principal | Politique appliquée | Justification |
|---|---|---|---|
| **S1 — Latence élevée** (Document Service répond en 8–15 s) | L'utilisateur attend, threads/connexions bloqués, effet domino | Timeout strict (10 s) + circuit breaker ; fallback : afficher le cache si dispo | Un timeout libère les ressources ; le circuit breaker évite de saturer un service déjà en difficulté |
| **S2 — Serveur intermittent** (Search renvoie 503 une fois sur trois, rolling update) | Échecs aléatoires perçus comme pannes | Retry (max 2) sur 503 + **backoff exponentiel avec jitter** | Le retry absorbe les erreurs transitoires ; le jitter évite que tous les clients retentent en même temps (thundering herd) |
| **S3 — Duplication de requêtes** (double clic sur « Créer », réseau lent) | Deux documents identiques créés | **Idempotency-Key** (UUID généré côté client) ; aucun retry automatique sur POST | La clé permet au serveur de détecter et ignorer le doublon ; pas de retry auto car POST a un effet de bord |

## Backoff exponentiel + jitter

Délai avant le n-ième retry : `delay = min(base × 2^n, max_delay) + jitter`.

Le **jitter** (composante aléatoire) est essentiel : sans lui, tous les clients
réessaient au même instant et écrasent le service au moment où il se rétablit.

## Fallbacks possibles

- Recherche indisponible → retourner « service temporairement indisponible »
  pendant que l'upload continue de fonctionner (dégradation gracieuse).
- Donnée en cache → servir une version légèrement périmée plutôt qu'une erreur.

## Règle générale

On ne retente **que** les erreurs transitoires (5xx, erreurs réseau), jamais les
erreurs 4xx (qui sont des fautes du client et se reproduiront à l'identique). Un
POST ayant un effet de bord ne doit jamais être retenté automatiquement sans
clé d'idempotence.
