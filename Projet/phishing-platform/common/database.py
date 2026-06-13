"""
Couche d'acces a la base de donnees SQLite.

SQLite : zero serveur, un simple fichier -> ideal pour une demo locale.
Les requetes utilisent des parametres lies (?) et JAMAIS de concatenation
de chaines -> protection contre les injections SQL.

Tables :
- users        : comptes (login, hash du mot de passe, role)
- sessions     : tokens actifs (on stocke le HASH du token, pas le token)
- reports      : signalements d'e-mails suspects avec leur score
- audit_events : journal d'audit des actions sensibles
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from common.config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    login      TEXT NOT NULL,
    role       TEXT NOT NULL,
    issued_at  REAL NOT NULL,
    expires_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sender        TEXT NOT NULL,
    subject       TEXT,
    body          TEXT,
    urls          TEXT,
    submitted_by  TEXT NOT NULL,
    submitted_at  TEXT NOT NULL DEFAULT (datetime('now')),
    risk_score    INTEGER NOT NULL,
    risk_level    TEXT NOT NULL,
    justification TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT NOT NULL DEFAULT (datetime('now')),
    actor      TEXT,
    action     TEXT NOT NULL,
    outcome    TEXT NOT NULL,
    details    TEXT
);

CREATE INDEX IF NOT EXISTS idx_reports_sender ON reports(sender);
CREATE INDEX IF NOT EXISTS idx_reports_level  ON reports(risk_level);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Connexion SQLite avec acces par nom de colonne, commit/rollback auto."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Cree les tables si elles n'existent pas encore."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def reset_db() -> None:
    """Supprime toutes les donnees (tests et demo)."""
    with get_connection() as conn:
        conn.executescript(
            "DROP TABLE IF EXISTS users;"
            "DROP TABLE IF EXISTS sessions;"
            "DROP TABLE IF EXISTS reports;"
            "DROP TABLE IF EXISTS audit_events;"
        )
        conn.executescript(SCHEMA)
