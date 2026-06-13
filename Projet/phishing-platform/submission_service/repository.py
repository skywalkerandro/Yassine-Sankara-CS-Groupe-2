"""
Acces aux donnees pour les signalements (table reports).
Requetes parametrees uniquement (anti-injection SQL).
"""
from __future__ import annotations

import json
from typing import Optional

from common.database import get_connection


def save_report(sender: str, subject: str, body: str, urls: list,
                submitted_by: str, score: int, level: str, justification: str) -> int:
    """Enregistre un signalement analyse. Renvoie son identifiant."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO reports "
            "(sender, subject, body, urls, submitted_by, risk_score, risk_level, justification) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sender, subject, body, json.dumps(urls), submitted_by, score, level, justification),
        )
        return cur.lastrowid


def list_reports(limit: int = 50) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, sender, subject, submitted_by, submitted_at, risk_score, risk_level "
            "FROM reports ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_report(report_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        try:
            data["urls"] = json.loads(data.get("urls") or "[]")
        except (json.JSONDecodeError, TypeError):
            data["urls"] = []
        return data


def search_reports(sender: str = "", level: str = "", keyword: str = "",
                   limit: int = 50) -> list:
    """Recherche par expediteur, niveau et/ou mot-cle. Criteres combines en ET."""
    clauses = []
    params: list = []
    if sender:
        clauses.append("sender LIKE ?")
        params.append(f"%{sender}%")
    if level:
        clauses.append("risk_level = ?")
        params.append(level)
    if keyword:
        clauses.append("(subject LIKE ? OR body LIKE ?)")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    query = (
        "SELECT id, sender, subject, submitted_by, submitted_at, risk_score, risk_level "
        "FROM reports" + where + " ORDER BY id DESC LIMIT ?"
    )
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
