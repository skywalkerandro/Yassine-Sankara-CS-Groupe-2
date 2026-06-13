# TP — Applications Réparties et Cybersécurité

Recueil des travaux pratiques (partie **TP Guidé**) pour le module
*Applications Réparties et Cybersécurité*. Les quatre séances partagent le même
**projet fil rouge** : un Système de Gestion Documentaire Distribué
(`DocumentService`).

## Auteur

Sankara Kabem Yassine

## Objectifs

Construire et sécuriser progressivement un système documentaire distribué :
des concepts d'architecture (séance 5), à la conception d'API fiable
(séance 6), à la sérialisation des données (séance 7), jusqu'à l'invocation
d'objets distants (séance 10).

## Technologies utilisées

- **Python 3** (bibliothèque standard : `json`, `dataclasses`, `re`, `logging`)
- **Protocol Buffers** (`protobuf` + `protoc`)
- **Pyro5** (objets distants) + serpent

## Organisation du dépôt

```
TP/
├── README.md                          # ce fichier
├── seance05_concepts_distribues/      # conceptuel : architecture + sécurité
│   ├── README.md                      # présentation + sommaire
│   ├── TP5.1_architecture.md
│   ├── TP5.2_analyse_defis.md
│   ├── TP5.3_surfaces_attaque.md
│   └── architecture_sgdd.svg
├── seance06_apis_fiabilite/           # conceptuel : contrat d'API + résilience
│   ├── README.md                      # présentation + sommaire
│   ├── TP6.1_contrat_api.md
│   ├── TP6.2_fiabilite_client.md
│   └── TP6.3_modele_securite.md
├── seance07_serialisation/            # code : JSON, versioning, Protobuf
│   ├── README.md
│   ├── tp7_1_contrat_json.py
│   ├── tp7_2_versioning.py
│   ├── tp7_3_protobuf.py
│   ├── document.proto
│   └── document_pb2.py
└── seance10_objets_distants/          # code : Pyro5 (serveur/client distribué)
    ├── README.md
    ├── server_docs.py
    ├── client_docs.py
    └── run_demo.py
```

## Aperçu des séances

| Séance | Sujet | Nature | Livrables principaux |
|---|---|---|---|
| 5 | Concepts des systèmes distribués | Conceptuel | Schéma d'architecture, analyse des défis, cartographie des surfaces d'attaque |
| 6 | Communication, APIs et fiabilité | Conceptuel | Contrat d'API, politiques de fiabilité (timeout/retry/backoff), modèle de sécurité |
| 7 | Sérialisation et marshalling | Code | Contrat JSON validé, versioning v1/v2, Protobuf, politique `pickle` |
| 10 | Invocation d'objets distants | Code | `DocumentService` Pyro5 (serveur + client), durcissement sécurité |

## Comment exécuter le code

Chaque séance avec du code possède son propre `README.md` détaillé. En résumé :

```bash
# Séance 7
cd seance07_serialisation
pip install protobuf
protoc --python_out=. document.proto      # régénère document_pb2.py
python3 tp7_1_contrat_json.py
python3 tp7_2_versioning.py
python3 tp7_3_protobuf.py

# Séance 10
cd ../seance10_objets_distants
pip install Pyro5
python3 run_demo.py                        # lance NS + serveur + client
```

Les séances 5 et 6 sont conceptuelles : chaque livrable est dans son propre
fichier (`TP5.1_*.md`, `TP6.1_*.md`, etc.), et le `README.md` de la séance sert
de sommaire qui pointe vers eux.

## Fil conducteur de sécurité

Un même principe traverse les quatre séances : **ne jamais faire confiance à
l'entrée** (Zero Trust). Concrètement — validation stricte en *fail closed*,
messages d'erreur génériques côté client avec détail dans les logs serveur,
sérialiseurs inertes (JSON / Serpent, jamais `pickle` sur entrée réseau), et
exposition minimale des méthodes (moindre privilège).
