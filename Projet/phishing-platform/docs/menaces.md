# Tableau des menaces principales et contre-mesures

Analyse des risques de securite de la plateforme et des protections mises en
place. Approche *security by design* : la securite est integree des la
conception, pas ajoutee apres coup.

## Tableau de synthese

| # | Menace | Scenario d'attaque | Contre-mesure implementee | Ou (fichier) |
|---|--------|--------------------|--------------------------|--------------|
| 1 | **Vol de mots de passe** | Fuite de la base -> mots de passe lisibles | Hachage PBKDF2-HMAC-SHA256, sel aleatoire par utilisateur, 200 000 iterations. Jamais stockes ni logges en clair. | `common/security.py` |
| 2 | **Vol / rejeu de tokens** | Interception ou fuite de tokens de session | On stocke le **hash SHA-256** du token, pas le token. Tokens jamais journalises en entier (`mask_token`). Expiration (TTL) des sessions. | `common/security.py`, `auth_service/repository.py` |
| 3 | **Injection SQL** | `login = "'; DROP TABLE users;--"` | Requetes **parametrees** (`?`) partout, jamais de concatenation. Validation du format du login. | `*/repository.py`, `common/validation.py` |
| 4 | **Entrees malveillantes / XSS stocke** | Caracteres de controle, payloads dans le corps | Validation et **nettoyage** systematique cote serveur (retrait des caracteres de controle, verification de type et de format). | `common/validation.py` |
| 5 | **Deni de service par volumetrie** | Corps de requete enorme, milliers d'URLs | **Limitation de taille** (corps <= 64 Ko, body <= 20 Ko, <= 50 URLs). Rejet HTTP 413. | `common/config.py`, `common/service_base.py` |
| 6 | **Abus d'appels (flood)** | Bombardement de requetes | **Rate limiting** par IP (fenetre glissante, 60 req/min par defaut). Rejet HTTP 429. | `common/service_base.py` |
| 7 | **Execution de code a la deserialisation** | Payload malveillant deserialise (cas classique de `pickle`) | Pyro5 configure avec le serializer **serpent** : ne deserialise que des types de base, pas d'objets arbitraires. Aucun usage de `pickle`. JSON cote HTTP. | `analysis_service/server.py` |
| 8 | **Acces non autorise** | Appel direct d'un endpoint sans authentification | Verification du token sur chaque route protegee (`require_auth`). Acces refuse -> HTTP 403/401. | `submission_service/auth_client.py` |
| 9 | **Elevation de privileges** | Un analyste tente d'acceder a l'audit | **Controle de role** (`require_role(admin)`). L'audit est reserve a l'administrateur. | `submission_service/server.py` |
| 10 | **Fuite d'information par les erreurs** | Messages d'erreur reveLant la stack, la structure interne | **Messages generiques** cote client ("Erreur interne"). Le detail est logge cote serveur uniquement. | `common/service_base.py` |
| 11 | **Enumeration de comptes** | Difference de message entre "login inconnu" et "mauvais mot de passe" | Message **identique** dans les deux cas ("Identifiants invalides"). Hachage factice pour egaliser le temps de reponse. | `auth_service/server.py`, `auth_service/repository.py` |
| 12 | **Indisponibilite en cascade** | Un service tombe -> tout s'effondre | **Timeout** sur chaque appel distant (5 s). Indisponibilite geree proprement (HTTP 503). L'audit est best-effort (n'empeche pas l'operation). | `common/http_client.py`, `submission_service/` |
| 13 | **Attaque temporelle (timing)** | Mesure du temps de comparaison pour deviner un secret | Comparaisons en **temps constant** (`hmac.compare_digest`). | `common/security.py` |

## Menaces identifiees mais hors perimetre (pistes)

Ces points depassent le cadre d'un projet pedagogique demontrable localement,
mais sont mentionnes par honnetete :

- **Chiffrement du transport (TLS/HTTPS)** : ici tout est en local (127.0.0.1).
  En production, il faudrait du HTTPS entre client et Gateway et du TLS entre
  services.
- **Stockage chiffre de la base** : SQLite n'est pas chiffre. En production,
  envisager SQLCipher ou un chiffrement au niveau disque.
- **Rotation et revocation fine des tokens** : on a l'expiration et le logout ;
  une vraie solution utiliserait des jetons signes (JWT) avec rotation.
- **Protection CSRF** : non pertinente pour un client natif/CLI, le deviendrait
  pour une interface web.
- **Journalisation centralisee et inviolable** : les logs sont locaux ; en
  production, les envoyer vers un collecteur en append-only.

## Principes transverses appliques

1. **Defense en profondeur** : la validation est faite a la Gateway *et*
   re-faite dans AnalysisService. Un service ne fait jamais confiance a son
   appelant.
2. **Moindre privilege** : chaque service n'a que les responsabilites
   strictement necessaires. L'audit est isole.
3. **Securite par defaut** : les limites (taille, rate) et l'expiration des
   sessions sont actives sans configuration.
4. **Minimisation des donnees sensibles** : ni mot de passe ni token complet ne
   transitent dans les logs.
