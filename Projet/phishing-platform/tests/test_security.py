"""Tests unitaires des fonctions de securite (sans reseau)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import security
from common.validation import (
    validate_sender, validate_login, validate_urls, ValidationError,
)


def test_password_jamais_en_clair():
    h = security.hash_password("monSecret123")
    assert "monSecret123" not in h
    assert h.startswith("pbkdf2_")


def test_verify_password_correct_et_incorrect():
    h = security.hash_password("bon")
    assert security.verify_password("bon", h) is True
    assert security.verify_password("mauvais", h) is False


def test_hash_password_sel_aleatoire():
    # Deux hash du meme mot de passe doivent differer (sel different).
    assert security.hash_password("x") != security.hash_password("x")


def test_token_masque_ne_revele_pas_tout():
    token = security.generate_token()
    masque = security.mask_token(token)
    assert token not in masque
    assert "masque" in masque


def test_hash_token_irreversible():
    token = "abc123"
    assert security.hash_token(token) != token
    assert len(security.hash_token(token)) == 64  # SHA-256 hex


def test_validation_rejette_email_invalide():
    try:
        validate_sender("pas-un-email")
        assert False, "aurait du lever"
    except ValidationError:
        pass


def test_validation_rejette_login_avec_caracteres_speciaux():
    try:
        validate_login("robert'; DROP TABLE users;--")
        assert False, "aurait du lever"
    except ValidationError:
        pass


def test_validation_borne_nombre_urls():
    many = [f"http://site{i}.com" for i in range(200)]
    result = validate_urls(many)
    assert len(result) <= 50


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t(); print(f"  [OK]    {t.__name__}"); passed += 1
        except AssertionError as e:
            print(f"  [ECHEC] {t.__name__}: {e}")
        except Exception:
            print(f"  [ERREUR] {t.__name__}"); traceback.print_exc()
    print(f"\n{passed}/{len(tests)} tests passes.")
    sys.exit(0 if passed == len(tests) else 1)
