# TP5.3 — Cartographie des surfaces d'attaque

Projet fil rouge : Système de Gestion Documentaire Distribué (SGDD)

## Objectif

Identifier toutes les surfaces d'attaque de l'architecture SGDD et proposer des
mesures de protection initiales, en appliquant les principes Zero Trust.

## Matrice des surfaces d'attaque

| Surface | Menace | Contrôle | Priorité |
|---|---|---|---|
| API externe (endpoints via Gateway) | Injection, brute force, DDoS applicatif | Validation stricte, rate limiting, TLS | Critique |
| Communications inter-services | Mouvement latéral, usurpation de service | mTLS ou tokens de service, segmentation réseau | Élevée |
| Bases de données | Accès direct, credentials exposés, ports ouverts | Réseau privé, secrets gérés (vault), moindre privilège | Critique |
| Interface d'administration | Élévation de privilèges, accès non autorisé | AuthZ stricte (rôle admin), MFA, audit renforcé | Critique |
| Logs et traces | Fuite de données sensibles (tokens, PII) | Masquage des secrets, rétention limitée | Moyenne |
| Sérialisation (échanges) | Désérialisation non sécurisée (RCE) | Formats inertes (JSON), validation, jamais `pickle` réseau | Élevée |

## Application des principes Zero Trust

- **Ne jamais faire confiance, toujours vérifier** : chaque appel inter-service
  est authentifié, même à l'intérieur du réseau.
- **Moindre privilège** : chaque service n'accède qu'aux ressources strictement
  nécessaires (sa propre base, pas celle des autres).
- **Vérification continue** : tokens à durée de vie courte, validation à chaque requête.
- **Segmentation** : les bases ne sont jamais directement joignables depuis l'extérieur.

## Synthèse de la priorisation

Les surfaces classées **Critique** (API externe, bases de données, interface
d'admin) sont celles dont la compromission donne un accès direct aux données ou
aux privilèges élevés : elles doivent être traitées en premier. Les surfaces
**Élevée** (inter-services, sérialisation) concernent la propagation d'une
attaque déjà entamée (mouvement latéral, exécution de code). Les surfaces
**Moyenne** (logs) sont des vecteurs indirects mais réels de fuite d'information.
