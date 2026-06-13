# TP Séance 6 — Communication, APIs et Fiabilité (Python)

Module : Applications Réparties et Cybersécurité
Projet fil rouge : Système de Gestion Documentaire Distribué
Auteur : Sankara Kabem Yassine

## Objectifs du travail

Concevoir le contrat d'API du système documentaire, définir des politiques de
fiabilité côté client face aux pannes réseau (timeouts, retries, backoff,
idempotence), et établir un modèle de sécurité minimal. Séance **conceptuelle** :
les livrables sont des spécifications et des tableaux d'analyse.

## Concepts mobilisés

- Conception d'API REST (contrats, codes HTTP, versioning, idempotence, pagination)
- Patterns de résilience client (timeout, retry, backoff exponentiel + jitter)
- Modèle STRIDE, RBAC, rate limiting

## Livrables

| Livrable | Fichier | Contenu |
|---|---|---|
| TP6.1 | [`TP6.1_contrat_api.md`](TP6.1_contrat_api.md) | Contrat d'API complet (endpoints, codes, idempotence) |
| TP6.2 | [`TP6.2_fiabilite_client.md`](TP6.2_fiabilite_client.md) | Politiques de fiabilité + 3 scénarios de panne |
| TP6.3 | [`TP6.3_modele_securite.md`](TP6.3_modele_securite.md) | Modèle de sécurité + matrice STRIDE |

## Synthèse — 10 points à retenir

1. Un contrat d'API définit entrées, sorties, erreurs et garanties — c'est la base de l'interopérabilité.
2. Les codes HTTP ont un sens précis : 4xx = faute du client, 5xx = faute du serveur.
3. Versionner l'API (`/api/v1/`) permet de la faire évoluer sans casser les clients.
4. Idempotence : GET/PUT/DELETE le sont ; POST de création non → Idempotency-Key.
5. Toujours paginer les listes (éviter les réponses géantes).
6. Un timeout est indispensable : sans lui, un service lent bloque le client.
7. Retry uniquement sur erreurs transitoires (5xx, réseau), jamais sur 4xx.
8. Backoff exponentiel + jitter évite le thundering herd au rétablissement.
9. AuthN (qui) et AuthZ (quoi) sont deux contrôles distincts et complémentaires.
10. La sécurité se place en défense en profondeur : Gateway **et** service.
