# TP5.2 — Analyse des défis distribués

Projet fil rouge : Système de Gestion Documentaire Distribué (SGDD)

## Objectif

Pour chaque service du SGDD, analyser les défis distribués (cohérence,
tolérance aux pannes, latence) et proposer des solutions architecturales.

## Tableau d'analyse

| Composant | Défi | Risque concret | Proposition de solution |
|---|---|---|---|
| Auth Service | Disponibilité | Si Auth tombe, personne ne peut se connecter → tout le système bloqué | Réplication (2 instances), cache de tokens JWT côté Gateway |
| Stockage Service | Cohérence | Document uploadé mais pas encore indexé → invisible en recherche | File de messages pour la synchro ; cohérence éventuelle acceptable |
| Recherche Service | Latence | Indexation de gros documents lente → bloque le retour utilisateur | Indexation asynchrone (file), cache des recherches fréquentes |
| API Gateway | Disponibilité | Point unique de défaillance (SPOF) | Plusieurs instances derrière un load balancer |
| Base PostgreSQL (Auth) | Cohérence forte | Tokens incohérents → accès erronés | Cohérence forte obligatoire ici (pas de cohérence éventuelle) |
| Notifications | Tolérance aux pannes | Perte d'alertes si le service tombe | File durable ; notifications non critiques (fallback : ignorer) |

## Les trade-offs à retenir

Il n'existe pas de solution unique. Chaque pattern a un coût :

- Le **cache** améliore la latence mais pose le problème de l'invalidation.
- La **réplication** améliore la disponibilité mais complexifie la cohérence.
- La **file de messages** découple les services mais ajoute de la latence de traitement.
- Le **fallback** maintient le service en mode dégradé mais peut renvoyer des données périmées.
- Le **circuit breaker** protège un service en difficulté mais coupe temporairement une fonctionnalité.

On choisit consciemment selon le contexte : cohérence forte pour Auth,
cohérence éventuelle acceptable pour la recherche.

## Lien avec le théorème CAP

En cas de **partition réseau** (P), le SGDD fait des choix différents selon le
sous-système :

- **Recherche / lecture** : privilégie la **disponibilité** (A) — la cohérence
  éventuelle est tolérée (un résultat légèrement périmé vaut mieux qu'une erreur).
- **Authentification** : privilégie la **cohérence** (C) — un token doit être
  valide ou non, sans ambiguïté, quitte à refuser le service.

Différents sous-systèmes d'une même application peuvent donc adopter des
positionnements CAP distincts.
