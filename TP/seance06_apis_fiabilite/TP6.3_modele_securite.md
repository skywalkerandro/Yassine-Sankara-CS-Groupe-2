# TP6.3 — Sécurité API : modèle minimal

Projet fil rouge : Système de Gestion Documentaire Distribué

## Objectif

Définir les premières mesures de sécurité de l'API : mécanisme de token,
placement des contrôles, et cartographie des surfaces d'exposition.

## Mécanisme de token

- **Génération** : token signé (JWT) avec durée de vie courte (ex. 15 min) +
  refresh token.
- **Transmission** : header `Authorization: Bearer <token>`.
- **Vérification** : signature validée localement (JWT) ou via appel à Auth Service.
- **Invalidation** : expiration naturelle, logout (liste de révocation), rotation des clés.

## Placement des contrôles

| Contrôle | Niveau | Détail |
|---|---|---|
| Validation d'entrée | Gateway **et** service | Défense en profondeur : la Gateway filtre le gros, le service revalide |
| Rate limiting | Gateway | Sur `/auth/login` et `/search` (endpoints sensibles/coûteux) |
| Audit logs | Service | Login, échecs, suppressions, accès admin |

## Matrice « Surface → Menace → Contrôle »

| Surface | Menace principale | Contrôle proposé | Priorité |
|---|---|---|---|
| `/auth/login` | Brute force sur credentials | Rate limiting (5 tent./min/IP), verrouillage progressif, logs | Critique |
| `/documents` (POST) | Injection JSON, upload malveillant | Validation stricte, taille max, Content-Type vérifié | Critique |
| `/search` | DDoS applicatif (requêtes coûteuses) | Rate limiting, pagination obligatoire, timeout serveur | Élevée |
| Tous endpoints | MITM, interception de tokens | TLS obligatoire, HSTS | Critique |
| Inter-services auth ↔ documents | Mouvement latéral, usurpation | mTLS ou tokens de service | Élevée |
| Inter-services (tous) | Replay de requêtes internes | Nonces + timestamps + fenêtre de validité | Moyenne |
| Admin — gestion utilisateurs | Élévation de privilèges | AuthZ stricte (admin only), MFA, audit renforcé | Critique |
| Admin — stats / debug | Fuite d'informations sensibles | Non exposés en prod ou protégés réseau + auth | Élevée |

## Mini Threat Modeling — STRIDE appliqué

| Lettre | Menace | Exemple sur le SGDD |
|---|---|---|
| **S** Spoofing | Usurpation d'identité | Voler un token pour accéder aux documents d'autrui |
| **T** Tampering | Falsification | Modifier un document en transit (sans TLS) |
| **R** Repudiation | Déni d'action | Supprimer un document et nier l'avoir fait (sans audit log) |
| **I** Information Disclosure | Fuite de données | Traceback ou message d'erreur révélant la structure interne |
| **D** Denial of Service | Déni de service | Requêtes de recherche coûteuses répétées |
| **E** Elevation of Privilege | Élévation de privilèges | Un utilisateur « viewer » accédant aux endpoints admin |

## AuthN vs AuthZ — clarification

- **AuthN (authentification)** : vérifie *qui* tu es (token valide).
- **AuthZ (autorisation)** : vérifie *ce que* tu as le droit de faire (rôle,
  propriété de la ressource).

Les deux sont nécessaires et distincts : un utilisateur peut être authentifié
(token valide) mais non autorisé (403) à accéder à un document qui n'est pas le sien.
