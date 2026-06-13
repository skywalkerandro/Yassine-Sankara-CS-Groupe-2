# TP Séance 5 — Concepts des Systèmes Distribués (Python)

Module : Applications Réparties et Cybersécurité
Projet fil rouge : Système de Gestion Documentaire Distribué (SGDD)
Auteur : Sankara Kabem Yassine

## Objectifs du travail

Concevoir l'architecture d'un système documentaire distribué, analyser ses
défis (cohérence, tolérance aux pannes, latence) et cartographier ses surfaces
d'attaque. Séance **conceptuelle** : les livrables sont des schémas et des
tableaux d'analyse, pas du code.

## Concepts mobilisés

- Architecture client–serveur et microservices
- Théorème CAP, modèles de cohérence
- Patterns de résilience (cache, réplication, file de messages, fallback, circuit breaker)
- Principes Zero Trust

## Contexte du projet fil rouge

Le SGDD doit gérer des documents pour des centaines d'utilisateurs simultanés,
garantir la disponibilité, et respecter des contraintes de sécurité (documents
confidentiels, audit d'accès, conformité RGPD).

## Livrables

| Livrable | Fichier | Contenu |
|---|---|---|
| TP5.1 | [`TP5.1_architecture.md`](TP5.1_architecture.md) + [`architecture_sgdd.svg`](architecture_sgdd.svg) | Architecture logique et physique + schéma |
| TP5.2 | [`TP5.2_analyse_defis.md`](TP5.2_analyse_defis.md) | Analyse des défis distribués par composant |
| TP5.3 | [`TP5.3_surfaces_attaque.md`](TP5.3_surfaces_attaque.md) | Cartographie des surfaces d'attaque |

## Synthèse — 10 points à retenir

1. Un système distribué = composants sur des machines distinctes coordonnés par le réseau.
2. Distribution ≠ parallélisme ≠ concurrence (objectifs et contraintes différents).
3. Pas d'horloge globale → l'ordre des événements est ambigu.
4. Les pannes sont **partielles** : un service peut tomber pendant que les autres tournent.
5. La latence est variable (jitter) et le réseau peut se partitionner.
6. Théorème CAP : en cas de partition, choisir entre cohérence et disponibilité.
7. Différents sous-systèmes peuvent faire des choix CAP différents.
8. Les patterns de résilience (cache, réplication, file, fallback, circuit breaker) ont des trade-offs.
9. Distribuer étend la surface d'attaque → Zero Trust devient nécessaire.
10. Architecture logique (services) ≠ architecture physique (machines/conteneurs).
