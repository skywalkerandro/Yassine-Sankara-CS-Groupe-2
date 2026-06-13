# TP Séance 10 — Invocation d'Objets Distants en Python (Pyro5)

Module : Applications Réparties et Cybersécurité
Projet fil rouge : DocumentService (équivalent RMI en Python)

## Objectifs du travail

Créer un objet distant `DocumentService` publié dans un name server et consommé
par un client proxy, puis le durcir : politique d'exposition des méthodes,
validation stricte des entrées avec erreurs sûres, et minimisation de la
surface d'attaque liée à la sérialisation.

## Technologies utilisées

- Python 3
- Pyro5 (Python Remote Objects) + serpent (sérialiseur sûr)

## Structure du dossier

```
seance10_objets_distants/
├── README.md          # ce fichier (contient TP10.2, 10.3, 10.4 + Lab)
├── server_docs.py     # TP10.1–10.4 — DocumentService distant durci
├── client_docs.py     # client : proxy + cas nominaux + cas d'erreur
└── run_demo.py        # orchestrateur (name server + serveur + client)
```

## Instructions pour exécuter

```bash
pip install Pyro5
```

**Méthode recommandée (3 terminaux), dans cet ordre :**

```bash
# Terminal 1 — name server
python3 -m Pyro5.nameserver

# Terminal 2 — serveur
python3 server_docs.py

# Terminal 3 — client
python3 client_docs.py
```

**Méthode automatique (un seul terminal)** — lance les trois en sous-processus :

```bash
python3 run_demo.py
```

---

## TP10.1 — Service distant de gestion de documents

`DocumentService` est une classe décorée `@Pyro5.api.expose`, enregistrée
auprès du name server sous le nom logique `tp10.documents.service`.

### Méthodes implémentées

| Méthode | Paramètres | Retour | Comportement |
|---|---|---|---|
| `list_documents()` | aucun | `list[str]` | Liste des IDs de documents |
| `get_document_content(doc_id)` | `doc_id: str` | `str` | Contenu, lève `KeyError` si absent |

### Sortie d'exécution obtenue (`run_demo.py`)

```
list_documents() -> ['doc_001', 'doc_002', 'doc_003']
get_document_content('doc_001') -> Rapport annuel 2024 — données confidentielles
```

### Checklist de validation TP10.1

- [x] Le name server est démarré avant le serveur
- [x] `list_documents()` retourne une liste non vide
- [x] `get_document_content("doc_001")` retourne le bon texte
- [x] Un `doc_id` inexistant lève une exception côté client
- [x] Le serveur journalise chaque appel entrant

### Schéma d'architecture (ASCII)

```
  +----------+        lookup()         +-------------+
  |  CLIENT  | ----------------------> | NAME SERVER |
  | (proxy)  | <---- URI de l'objet -- |  (registre) |
  +----------+                         +-------------+
       |                                      ^
       |  appel de méthode distante           | register("tp10.documents.service")
       |  (get_document_content, ...)         |
       v                                      |
  +-----------------------------+             |
  |  SERVEUR (daemon Pyro5)      | -----------+
  |  DocumentService            |
  |   _DOCUMENTS = {...}        |
  +-----------------------------+
```

---

## TP10.2 — Politique d'exposition et sécurité du service

On distingue explicitement les méthodes **publiques** (métier) des méthodes
**internes** (administration / accès données). Pyro5 n'expose jamais les
méthodes préfixées par underscore.

### Tableau de politique d'exposition

| Méthode | Exposée ? | Pourquoi | Risque si exposée sans contrôle |
|---|---|---|---|
| `list_documents()` | Oui | Navigation client | Fuite de noms de fichiers internes |
| `get_document_content()` | Oui — avec validation | Service principal | Path traversal, accès non autorisé |
| `admin_reload_index()` | Oui — **token requis** | Admin contrôlée (démo) | DoS si non protégée |
| `_reload_index()` | Non | Opération d'administration | DoS, corruption d'état |
| `_check_token()` | Non | Vérification interne | Contournement d'authentification |
| `_db_connect()` | **Jamais** | Accès base de données | Compromission totale du stockage |

### Vérification obtenue

Test automatique de la surface exposée :

```
Méthodes exposées: ['admin_reload_index', 'get_document_content', 'list_documents']
  OK: _reload_index inaccessible (AttributeError)
  OK: _db_connect  inaccessible (AttributeError)
  OK: _check_token inaccessible (AttributeError)
```

### Contrôle d'accès (token) — résultat

```
bon token   -> index rechargé
mauvais tok -> PermissionError: Accès refusé
```

### Note sécurité (politique d'exposition)

Seules les trois méthodes métier sont accessibles à distance. Toute opération
sensible (rechargement d'index) exige un token vérifié **avant** traitement ; un
token invalide est journalisé et rejeté avec un message générique. Les accès au
stockage (`_db_connect`) ne sont jamais exposés : leur compromission équivaudrait
à la compromission totale du service. Le principe est le moindre privilège —
n'exposer que ce qui est strictement nécessaire au client.

---

## TP10.3 — Validation stricte des entrées et erreurs sûres

Règles appliquées sur `doc_id` :

- **Type** : doit être `str`
- **Longueur** : 3 à 32 caractères
- **Format** : `^[A-Za-z0-9_]+$` (alphanumérique + underscore)
- **Valeurs interdites** : `..`, `/`, `;` → bloquées par le format
- **Message client** : toujours générique (jamais de chemin/nom interne)
- **Log serveur** : toujours détaillé (valeur reçue, type, contexte)

### Tableau de cas de test (résultats obtenus côté client)

| Entrée testée | Type | Résultat | Réponse côté client |
|---|---|---|---|
| `"doc_001"` | str | Accepté | Contenu du document |
| `"doc_999"` | str | Géré (`KeyError`) | `Document introuvable` |
| `"../../etc"` | str | Rejeté (format) | `Identifiant invalide` |
| `12345` | int | Rejeté (type) | `Paramètre invalide` |
| `""` | str | Rejeté (longueur) | `Identifiant invalide` |
| `"a"*100` | str | Rejeté (trop long) | `Identifiant invalide` |
| `None` | NoneType | Rejeté (type) | `Paramètre invalide` |
| `"doc;DROP"` | str | Rejeté (format) | `Identifiant invalide` |

Les tentatives de **path traversal** (`../../etc`) et d'**injection**
(`doc;DROP`) sont bloquées par la validation de format. Le client ne reçoit
jamais d'information système.

---

## TP10.4 — Surface d'attaque et sérialisation sûre

Le serveur force le sérialiseur **Serpent** (`Pyro5.config.SERIALIZER = "serpent"`)
— jamais `pickle`. Seuls des types primitifs traversent le réseau.

### Checklist « Safe Remote Object Calls »

- [x] Sérialiseur Serpent (défaut Pyro5) — jamais `pickle` en production
- [x] Paramètres : types primitifs uniquement (`str, int, float, bool, list, dict`)
- [x] Retours : types simples — pas d'objets Python complexes
- [x] Aucun objet fichier, socket ou connexion DB transmis
- [x] Aucune structure récursive profonde ou graphe d'objets
- [x] Validation du type et de la taille de chaque paramètre avant traitement
- [x] Journalisation de tout paramètre rejeté avec contexte
- [x] Pas de lambda, callable ou code transmis comme argument

### Matrice de surface d'attaque

| Surface | Risque | Contrôle | Priorité |
|---|---|---|---|
| Paramètres des méthodes exposées | Injection, type confusion, overflow | Validation type/format/longueur | CRITIQUE |
| Sérialiseur (`pickle`) | Exécution de code arbitraire (RCE) | Utiliser Serpent ; bannir `pickle` | CRITIQUE |
| Name server exposé | Enregistrement d'objets frauduleux | Filtrage IP, authentification NS | ÉLEVÉ |
| Méthodes décorées | Exposition accidentelle | Audit de la liste `@expose` | ÉLEVÉ |
| Exceptions distantes | Fuite d'informations internes | Wrapper + log interne | MOYEN |
| Retours des méthodes | Fuite de données sensibles | Filtrer les champs retournés | MOYEN |
| Port du daemon | Accès non autorisé réseau | Firewall, écoute locale si possible | MOYEN |

---

## Lab Sécurité — Mini étude de menaces (DocumentService)

| Scénario | Danger | Correction appliquée |
|---|---|---|
| `_reload_index` reçoit `@expose` par erreur | Un client peut vider le cache / saturer le serveur | Pas de `@expose` ; test vérifiant la non-exposition |
| `pickle` utilisé comme sérialiseur | Exécution de code arbitraire | Serpent forcé en configuration |
| `doc_id` non validé | Path traversal, injection | Validation format/longueur/type avant traitement |
| Traceback Python renvoyé au client | Fuite d'infos internes | Messages génériques + détail dans les logs |
| Name server accessible publiquement | Enregistrement d'objets malveillants | Restreindre l'écoute (localhost) + filtrage réseau |

---

## Synthèse — 10 points à retenir

1. L'invocation d'objet distant fait apparaître l'appel réseau comme un appel local.
2. Le name server découple le client de l'adresse physique de l'objet (URI).
3. L'ordre de démarrage est : name server → serveur → client.
4. Une méthode sans `@expose` (ou préfixée `_`) n'est pas accessible à distance.
5. Toujours valider les paramètres reçus avant traitement (zero trust).
6. Le client reçoit un message générique ; le détail reste dans les logs serveur.
7. Le path traversal et l'injection se bloquent par validation de format stricte.
8. Le sérialiseur par défaut sûr de Pyro5 est Serpent — jamais `pickle`.
9. Seuls des types primitifs doivent traverser le réseau.
10. La surface d'attaque se réduit en n'exposant que le strict nécessaire (moindre privilège).
