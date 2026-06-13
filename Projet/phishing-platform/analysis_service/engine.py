"""
Moteur d'analyse heuristique de phishing.

Principe : un score CUMULATIF base sur des regles EXPLICABLES. Chaque regle
qui se declenche ajoute des points et une justification textuelle. Le total
est ensuite traduit en niveau : faible / moyen / eleve.

Ce moteur est volontairement simple et transparent (pas de boite noire) :
chaque decision peut etre justifiee a l'utilisateur, ce qui est l'esprit
de l'enonce.

Regles implementees :
1. Mots/expressions d'urgence ou de manipulation
2. Demande d'informations sensibles (identifiants, paiement)
3. URLs presentes (et nombre)
4. Domaines suspects : TLD a risque, IP brute, raccourcisseurs, sous-domaines trompeurs
5. Ecart entre le domaine de l'expediteur et les domaines des liens
6. Mention de pieces jointes
7. Adresse expediteur imitant une marque connue (typosquatting simple)
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# --- Listes de reference (pedagogiques, non exhaustives) ------------------

URGENT_WORDS = [
    "urgent", "immediatement", "immediat", "expire", "expiration", "suspendu",
    "suspendre", "bloque", "bloquer", "verifiez", "verifier", "confirmez",
    "confirmer", "action requise", "derniere chance", "attention", "alerte",
    "compte sera", "sous 24", "sous 48", "delai", "maintenant", "rapidement",
]

SENSITIVE_REQUESTS = [
    "mot de passe", "identifiant", "numero de carte", "carte bancaire",
    "code pin", "code secret", "coordonnees bancaires", "rib", "iban",
    "securite sociale", "validez vos informations", "mettre a jour vos informations",
    "cliquez ici pour vous connecter",
]

# TLD souvent associes a des campagnes a bas cout (indicateur, pas une preuve).
SUSPICIOUS_TLDS = {
    "zip", "review", "country", "kim", "cricket", "science", "work", "party",
    "gq", "ml", "cf", "tk", "top", "xyz", "click", "link",
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly", "shorturl.at",
}

# Marques frequemment usurpees. On detecte les imitations approximatives.
KNOWN_BRANDS = [
    "paypal", "microsoft", "apple", "google", "amazon", "netflix", "orange",
    "free", "sfr", "laposte", "impots", "ameli", "banque", "bnp", "creditmutuel",
]

_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def _domain_of_email(email: str) -> str:
    """Extrait le domaine d'une adresse e-mail."""
    if "@" in email:
        return email.split("@", 1)[1].lower().strip()
    return ""


def _domain_of_url(url: str) -> str:
    """Extrait le domaine (host) d'une URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        # Retire un eventuel port et les identifiants user:pass@.
        if "@" in netloc:
            netloc = netloc.split("@", 1)[1]
        if ":" in netloc:
            netloc = netloc.split(":", 1)[0]
        return netloc
    except Exception:
        return ""


def _registrable_domain(host: str) -> str:
    """
    Approximation du domaine enregistrable (les 2 derniers labels).
    Suffisant pour la demo : 'login.paypal.com' -> 'paypal.com'.
    """
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _tld_of(host: str) -> str:
    parts = host.split(".")
    return parts[-1] if parts else ""


def _levenshtein(a: str, b: str) -> int:
    """Distance d'edition simple (pour detecter le typosquatting)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def analyze(sender: str, subject: str, body: str, urls: list[str],
            has_attachment: bool = False) -> dict:
    """
    Analyse un e-mail et renvoie un dictionnaire :
    {
        "score": int,
        "level": "faible"|"moyen"|"eleve",
        "reasons": [str, ...],
        "indicators": {...}   # details structures
    }
    """
    score = 0
    reasons: list[str] = []
    text = f"{subject}\n{body}".lower()

    sender_domain = _domain_of_email(sender)
    sender_reg = _registrable_domain(sender_domain) if sender_domain else ""

    # --- Regle 1 : mots d'urgence / manipulation ---
    found_urgent = sorted({w for w in URGENT_WORDS if w in text})
    if found_urgent:
        pts = min(len(found_urgent) * 8, 24)
        score += pts
        apercu = ", ".join(found_urgent[:4])
        reasons.append(f"Vocabulaire d'urgence ou de pression detecte ({apercu}) [+{pts}]")

    # --- Regle 2 : demande d'informations sensibles ---
    found_sensitive = sorted({w for w in SENSITIVE_REQUESTS if w in text})
    if found_sensitive:
        pts = min(len(found_sensitive) * 12, 30)
        score += pts
        reasons.append(
            f"Demande d'informations sensibles ({found_sensitive[0]}...) [+{pts}]"
        )

    # --- Regle 3 : presence d'URLs ---
    url_domains = [d for d in (_domain_of_url(u) for u in urls) if d]
    if urls:
        pts = 5
        score += pts
        reasons.append(f"{len(urls)} lien(s) present(s) dans le message [+{pts}]")

    # --- Regle 4 : domaines suspects ---
    flagged_domains = []
    for host in url_domains:
        reg = _registrable_domain(host)
        if _IP_RE.match(host):
            score += 20
            flagged_domains.append(f"{host} (adresse IP brute)")
            reasons.append(f"Lien pointant vers une adresse IP brute : {host} [+20]")
        elif reg in URL_SHORTENERS:
            score += 12
            flagged_domains.append(f"{host} (raccourcisseur)")
            reasons.append(f"URL raccourcie masquant la destination : {host} [+12]")
        elif _tld_of(host) in SUSPICIOUS_TLDS:
            score += 10
            flagged_domains.append(f"{host} (TLD a risque)")
            reasons.append(f"Domaine avec extension a risque : {host} [+10]")

    # --- Regle 5 : ecart expediteur / domaines des liens ---
    if sender_reg and url_domains:
        link_regs = {_registrable_domain(h) for h in url_domains}
        # Si aucun lien ne partage le domaine de l'expediteur -> suspect.
        if sender_reg not in link_regs:
            score += 15
            reasons.append(
                f"Le domaine de l'expediteur ({sender_reg}) ne correspond a aucun "
                f"domaine des liens [+15]"
            )

    # --- Regle 6 : pieces jointes annoncees ---
    attachment_words = ["piece jointe", "ci-joint", "ci joint", "attachment", "facture jointe"]
    mentions_attachment = has_attachment or any(w in text for w in attachment_words)
    if mentions_attachment:
        score += 8
        reasons.append("Piece jointe annoncee ou presente [+8]")

    # --- Regle 7 : typosquatting de marque dans l'expediteur ---
    if sender_reg:
        sender_name = sender_reg.split(".")[0]
        for brand in KNOWN_BRANDS:
            dist = _levenshtein(sender_name, brand)
            if 0 < dist <= 2 and abs(len(sender_name) - len(brand)) <= 2:
                score += 18
                reasons.append(
                    f"L'expediteur '{sender_name}' imite la marque '{brand}' "
                    f"(difference de {dist} caractere(s)) [+18]"
                )
                break

    # --- Synthese : score -> niveau ---
    score = max(0, min(score, 100))
    if score >= 45:
        level = "eleve"
    elif score >= 20:
        level = "moyen"
    else:
        level = "faible"

    if not reasons:
        reasons.append("Aucun indicateur de risque notable detecte.")

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
        "indicators": {
            "sender_domain": sender_domain,
            "url_domains": url_domains,
            "flagged_domains": flagged_domains,
            "urgent_terms": found_urgent,
            "sensitive_requests": found_sensitive,
            "mentions_attachment": mentions_attachment,
        },
    }
