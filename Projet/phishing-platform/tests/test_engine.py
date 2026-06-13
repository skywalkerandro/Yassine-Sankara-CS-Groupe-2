"""Tests unitaires du moteur d'analyse (sans reseau)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis_service.engine import analyze


def test_phishing_evident_est_eleve():
    r = analyze(
        sender="securite@paypa1.tk",
        subject="URGENT compte suspendu",
        body="Confirmez votre mot de passe immediatement http://192.168.0.1/x sinon bloque",
        urls=["http://192.168.0.1/x"],
    )
    assert r["level"] == "eleve"
    assert r["score"] >= 45


def test_email_legitime_est_faible():
    r = analyze(
        sender="collegue@entreprise.com",
        subject="Compte rendu",
        body="Bonjour, voici le compte rendu. Bonne journee.",
        urls=[],
    )
    assert r["level"] == "faible"
    assert r["score"] < 20


def test_typosquatting_detecte():
    r = analyze("contact@paypa1.com", "Bonjour", "Texte neutre", [])
    joined = " ".join(r["reasons"]).lower()
    assert "imite la marque" in joined


def test_url_raccourcie_augmente_score():
    sans = analyze("a@b.com", "x", "texte", [])
    avec = analyze("a@b.com", "x", "texte", ["https://bit.ly/x"])
    assert avec["score"] > sans["score"]


def test_score_borne_a_100():
    r = analyze(
        sender="paypa1@scam.tk",
        subject="URGENT URGENT compte bloque suspendu expire",
        body="mot de passe carte bancaire code pin rib iban http://1.2.3.4/x ci-joint",
        urls=["http://1.2.3.4/x"],
        has_attachment=True,
    )
    assert 0 <= r["score"] <= 100


def test_ecart_expediteur_liens():
    r = analyze("service@banque.com", "info", "voir https://autre-domaine.xyz/x",
                ["https://autre-domaine.xyz/x"])
    joined = " ".join(r["reasons"]).lower()
    assert "ne correspond a aucun" in joined


if __name__ == "__main__":
    # Mini-runner sans dependance a pytest.
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  [OK]    {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  [ECHEC] {t.__name__}: {e}")
        except Exception:
            print(f"  [ERREUR] {t.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} tests passes.")
    sys.exit(0 if passed == len(tests) else 1)
