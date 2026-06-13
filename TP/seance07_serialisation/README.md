# TP Séance 7 — Sérialisation et Marshalling (Python)

Module : Applications Réparties et Cybersécurité
Projet fil rouge : Système de Gestion Documentaire Distribué (DocumentService)

## Objectifs du travail

Maîtriser la sérialisation de données pour un système distribué : définir un
contrat JSON formel et le valider strictement, faire évoluer un schéma sans
casser la compatibilité, utiliser Protocol Buffers, et formaliser une politique
de sérialisation sûre (gestion du danger `pickle`).

## Technologies utilisées

- Python 3 (`json`, `dataclasses`, `re`, `logging` — bibliothèque standard)
- Protocol Buffers (`protobuf` + compilateur `protoc`)

## Structure du dossier

```
seance07_serialisation/
├── README.md                  # ce fichier (contient TP7.4)
├── tp7_1_contrat_json.py      # TP7.1 — contrat + validation stricte + tests
├── tp7_2_versioning.py        # TP7.2 — compatibilité v1/v2 + matrice
├── tp7_3_protobuf.py          # TP7.3 — encode/decode + comparaison taille
├── document.proto             # schéma Protobuf
└── document_pb2.py            # généré par protoc (régénérable)
```

## Instructions pour exécuter

```bash
# TP7.1 — Contrat JSON + validation
python3 tp7_1_contrat_json.py

# TP7.2 — Versioning JSON
python3 tp7_2_versioning.py

# TP7.3 — Protobuf (régénérer le code si besoin)
pip install protobuf
protoc --python_out=. document.proto
python3 tp7_3_protobuf.py
```

---

## TP7.1 — Contrat JSON + validation stricte

Contrat formel implémenté pour deux entités, avec `@dataclass`, sérialisation
(exclusion des champs `None`/sensibles), désérialisation et validation
exhaustive en **fail closed** (tout champ non conforme → rejet total).

### Contrat — entité `Document`

| Champ | Type | Obligatoire | Règles de validation | Exemple |
|---|---|---|---|---|
| `id` | int | Oui | Entier positif, > 0 | `42` |
| `title` | str | Oui | 1–200 caractères, non vide après strip | `"Rapport Q1"` |
| `author` | str | Oui | 1–100 caractères | `"Alice Dupont"` |
| `tags` | list[str] | Non | 0–20 éléments, chaque tag 1–50 chars | `["finance"]` |
| `classification` | str | Non | Allowlist : `public, internal, confidential, secret` — défaut `internal` | `"confidential"` |
| `created_at` | str | Non | Format ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) | `"2026-01-15T10:30:00Z"` |

### Contrat — entité `UserPublic`

| Champ | Type | Obligatoire | Règles | Exemple |
|---|---|---|---|---|
| `username` | str | Oui | 3–30 chars, alphanumérique + underscore | `"alice_d"` |
| `display_name` | str | Oui | 1–100 chars | `"Alice Dupont"` |
| `role` | str | Oui | Allowlist : `viewer, editor, admin` | `"editor"` |

### Cas de test (résultats obtenus)

Le script exécute 7 cas (2 valides, 5 invalides) — tous conformes aux attentes :

| Cas | Attendu | Résultat |
|---|---|---|
| Document complet | Accepté | Accepté |
| Document minimal (defaults) | Accepté | Accepté |
| Champ obligatoire manquant (`author`) | Rejeté | Rejeté |
| Type erroné (`id` en string) | Rejeté | Rejeté |
| Valeur hors allowlist (`classification`) | Rejeté | Rejeté |
| `id` non positif | Rejeté | Rejeté |
| JSON malformé | Rejeté | Rejeté |

**Principe de sécurité appliqué** : le client ne reçoit qu'un message générique
(`"Données invalides"`), tandis que le détail (champ fautif, type reçu) part
uniquement dans les logs serveur — prévention de la divulgation d'information.

---

## TP7.2 — Versioning JSON (compatibilité v1 → v2)

Évolution du payload `Document` par **ajout de champs optionnels** :

- **v1** : `{id, title, author}`
- **v2** : ajoute `tags` (liste) et `classification` (allowlist)

Règles respectées : ajout OK, retrait interdit, changement de type interdit.

Un désérialiseur **v2 unique et tolérant** lit aussi les payloads v1 (champs
manquants → valeurs par défaut : `tags=[]`, `classification="internal"`).

### Décision sur les champs inconnus

Les champs inconnus (ex. `priority` envoyé par un producteur plus récent) sont
**ignorés mais journalisés**. Justification : c'est cette tolérance qui permet à
un lecteur ancien de survivre à un producteur récent (forward-compatibilité).
On loggue pour garder une trace en cas d'abus.

### Matrice de compatibilité (résultats obtenus)

| Version payload | Lecteur | Accepté ? | Raison | Risque |
|---|---|---|---|---|
| v1 | v2 | Oui | Champs manquants → défauts | Aucun |
| v2 complet | v2 | Oui | Tous champs valides | Aucun |
| v2 altéré (`classification="top_secret"`) | v2 | **Non** | Valeur hors allowlist | Injection de classification bloquée |
| v2 + champ inconnu (`priority`) | v2 | Oui | Champ inconnu ignoré + loggué | Faible (traçé) |

Seule une valeur **explicitement hors contrat** (allowlist) ou un **type
incorrect** provoque un rejet : on échoue fermé (fail closed).

---

## TP7.3 — Protocol Buffers (schéma + échange)

Schéma `document.proto` défini avec les champs `id, title, author, tags,
classification`, compilé avec `protoc`. Un champ `priority = 6` est ajouté pour
démontrer la compatibilité.

### Points cruciaux pour le versioning Protobuf

- Le **numéro de champ** (`= 1`, `= 2`, …) est l'identité binaire sur le réseau.
- On ne **réutilise jamais** un numéro retiré (utiliser `reserved`), sinon les
  anciens messages sont décodés avec le mauvais type → corruption silencieuse.
- Un lecteur qui ne connaît pas un champ l'**ignore silencieusement**
  (rétro/forward-compatibilité native).

### Comparaison de taille (mesures obtenues)

Mêmes données encodées dans les deux formats :

| Critère | JSON | Protobuf | Commentaire |
|---|---|---|---|
| Taille payload (octets) | 122 | 57 | Protobuf ≈ **2.14×** plus compact |
| Lisibilité | Humaine (texte) | Binaire opaque | JSON gagne |
| Validation de types | Applicative | Schéma `.proto` | Protobuf gagne |
| Compatibilité ajout champ | Manuelle | Native (n° champ) | Protobuf gagne |
| Tooling nécessaire | Aucun (stdlib) | `protoc` + lib | JSON gagne |

**Lecture** : Protobuf est plus compact et applique un schéma fort, au prix
d'un outillage (compilation `.proto`) et d'une perte de lisibilité. JSON reste
préférable pour les APIs publiques lisibles ; Protobuf pour les échanges
inter-services performants.

---

## TP7.4 — Politique « Pickle : où c'est acceptable, où c'est interdit »

`pickle.loads()` peut **exécuter du code arbitraire** lors de la reconstruction
d'objets : un payload forgé peut lancer des commandes système. C'est donc
interdit sur toute entrée non fiable.

### Tableau de politique de sérialisation

| Source des données | Format autorisé | Contrôles requis | Justification |
|---|---|---|---|
| API REST (entrée client) | JSON uniquement | Validation stricte, limite taille, auth | Entrée non fiable → format inerte obligatoire |
| Inter-services (réseau interne) | JSON ou Protobuf | mTLS, validation, HMAC | Réseau interne ≠ confiance totale (zero trust) |
| Cache local (même processus) | `pickle` autorisé | Données générées localement uniquement | Confiance totale, pas d'entrée externe |
| Fichier uploadé par utilisateur | JSON/CSV/XML (defused) | Limite taille, validation, sandbox | Jamais `pickle` : risque d'exécution de code |
| File de messages (Kafka/RabbitMQ) | JSON ou Protobuf | Schema registry, validation, signature | Producteurs multiples → format interopérable sûr |
| Stockage persistant (DB, fichier) | JSON ou Protobuf | Intégrité (HMAC/chiffrement), migration schéma | Données altérables entre écriture et lecture |

### Checklist « Safe Serialization Policy »

1. Interdire `pickle` / `marshal` / `shelve` pour toute entrée non fiable.
2. Utiliser `yaml.safe_load()` au lieu de `yaml.load()`.
3. Limiter la taille des payloads avant parsing (ex. 1 Mo max).
4. Valider chaque champ après désérialisation (type, longueur, allowlist).
5. Signer les données sérialisées si elles transitent ou sont stockées (HMAC).
6. Logger les échecs de désérialisation (sans données sensibles).
7. Versionner les contrats de données (champs optionnels, pas de breaking change).
8. Tester les cas limites : payload vide, géant, types incohérents, champs inconnus.
9. Revoir tout usage de `pickle` en code review (flag automatique si possible).
10. Documenter le format accepté à chaque point d'entrée (API doc, README).

---

## Synthèse — 10 points à retenir

1. Sérialisation = objet → octets ; marshalling ajoute les métadonnées de transport.
2. JSON n'a pas de type date natif → convention ISO 8601 explicite.
3. JSON est schema-less : le contrat est implicite et **doit** être validé par le code.
4. `pickle.loads()` sur entrée réseau = exécution de code arbitraire (RCE).
5. Protobuf ignore les champs inconnus → versioning progressif sûr.
6. « Fail closed » : en cas de doute, refuser plutôt qu'accepter.
7. XML expose XXE et bombes XML ; JSON n'a ni entités ni DTD.
8. Ne jamais réutiliser un numéro de champ Protobuf (utiliser `reserved`).
9. `yaml.safe_load()` restreint aux types de base et évite l'exécution de code.
10. Syntaxe + types valides ≠ données fiables : valider la **sémantique** (allowlist, bornes).
