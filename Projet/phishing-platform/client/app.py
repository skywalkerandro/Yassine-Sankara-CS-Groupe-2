"""
Application native (PySide6) : client de la plateforme de detection de phishing.

C'est le composant "Client" de l'architecture. Il fournit une interface
graphique (fenetre de connexion + onglets) et ne communique qu'avec l'API
Gateway via HTTP/JSON. Toute la logique distribuee est invisible pour l'usager.

Lancement : python -m client.app
Pre-requis : les services doivent tourner (python scripts/run_all.py).
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QCheckBox, QFrame, QSpinBox, QAbstractItemView,
)

from client.api import ApiClient, ApiError
from client.theme import STYLESHEET, RISK_COLORS


# --------------------------------------------------------------------------
# Fenetre de connexion
# --------------------------------------------------------------------------
class LoginDialog(QDialog):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.setWindowTitle("Connexion - Plateforme anti-phishing")
        self.setFixedSize(420, 360)
        self.setObjectName("root")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(8)

        title = QLabel("Plateforme anti-phishing")
        title.setObjectName("title")
        subtitle = QLabel("Authentifiez-vous pour acceder a la plateforme")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        layout.addWidget(QLabel("Identifiant"))
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("ex : analyste")
        layout.addWidget(self.login_edit)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Mot de passe"))
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd_edit.setPlaceholderText("••••••••")
        self.pwd_edit.returnPressed.connect(self._attempt_login)
        layout.addWidget(self.pwd_edit)

        layout.addSpacing(20)
        self.btn = QPushButton("Se connecter")
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self._attempt_login)
        layout.addWidget(self.btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f85149;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        layout.addStretch()

    def _attempt_login(self):
        login = self.login_edit.text().strip()
        password = self.pwd_edit.text()
        if not login or not password:
            self.error_label.setText("Veuillez saisir un identifiant et un mot de passe.")
            return
        self.btn.setEnabled(False)
        self.error_label.setText("")
        try:
            self.api.connect(login, password)
            self.accept()
        except ApiError as exc:
            self.error_label.setText(str(exc))
            self.btn.setEnabled(True)


# --------------------------------------------------------------------------
# Onglet : Soumettre un e-mail
# --------------------------------------------------------------------------
class SubmitTab(QWidget):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Colonne formulaire
        form = QVBoxLayout()
        form.setSpacing(8)
        form.addWidget(self._section("Signaler un e-mail suspect"))

        form.addWidget(QLabel("Expediteur declare"))
        self.sender = QLineEdit()
        self.sender.setPlaceholderText("ex : service@paypa1-securite.tk")
        form.addWidget(self.sender)

        form.addWidget(QLabel("Objet"))
        self.subject = QLineEdit()
        self.subject.setPlaceholderText("ex : URGENT : votre compte sera suspendu")
        form.addWidget(self.subject)

        form.addWidget(QLabel("Contenu du message"))
        self.body = QTextEdit()
        self.body.setPlaceholderText("Collez ici le texte de l'e-mail suspect...")
        self.body.setMinimumHeight(180)
        form.addWidget(self.body)

        self.attachment = QCheckBox("Une piece jointe etait presente")
        form.addWidget(self.attachment)

        form.addSpacing(8)
        self.submit_btn = QPushButton("Analyser et signaler")
        self.submit_btn.setObjectName("primary")
        self.submit_btn.clicked.connect(self._submit)
        form.addWidget(self.submit_btn)
        form.addStretch()

        # Colonne resultat
        self.result_panel = self._build_result_panel()

        left = QWidget()
        left.setLayout(form)
        left.setMaximumWidth(460)
        root.addWidget(left)
        root.addWidget(self.result_panel, 1)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        return lbl

    def _build_result_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#161b22; border:1px solid #30363d; border-radius:8px; }")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        self.result_title = QLabel("Resultat de l'analyse")
        self.result_title.setObjectName("sectionTitle")
        lay.addWidget(self.result_title)

        self.badge = QLabel("En attente")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet(
            "background:#21262d; border-radius:8px; padding:18px; font-size:20px; font-weight:700;"
        )
        lay.addWidget(self.badge)

        self.score_label = QLabel("")
        self.score_label.setObjectName("subtitle")
        lay.addWidget(self.score_label)

        lay.addWidget(QLabel("Justification :"))
        self.reasons = QTextEdit()
        self.reasons.setReadOnly(True)
        lay.addWidget(self.reasons, 1)
        return frame

    def _submit(self):
        sender = self.sender.text().strip()
        if not sender:
            QMessageBox.warning(self, "Champ requis", "L'expediteur est obligatoire.")
            return
        self.submit_btn.setEnabled(False)
        try:
            result = self.api.submit(
                sender=sender,
                subject=self.subject.text().strip(),
                body=self.body.toPlainText().strip(),
                urls=[],
                has_attachment=self.attachment.isChecked(),
            )
            self._show_result(result)
        except ApiError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
        finally:
            self.submit_btn.setEnabled(True)

    def _show_result(self, result: dict):
        level = result["level"]
        color = RISK_COLORS.get(level, "#8b949e")
        self.badge.setText(f"RISQUE {level.upper()}")
        self.badge.setStyleSheet(
            f"background:{color}; color:#0d1117; border-radius:8px; "
            f"padding:18px; font-size:20px; font-weight:700;"
        )
        self.score_label.setText(f"Score de risque : {result['score']} / 100   (signalement #{result['id']})")
        self.reasons.setPlainText("\n".join(f"• {r}" for r in result["reasons"]))


# --------------------------------------------------------------------------
# Onglet : Historique
# --------------------------------------------------------------------------
class HistoryTab(QWidget):
    COLS = ["ID", "Niveau", "Score", "Expediteur", "Objet", "Par", "Date"]

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Historique des signalements")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        refresh = QPushButton("Rafraichir")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        lay.addLayout(header)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self._open_detail)
        lay.addWidget(self.table)

        hint = QLabel("Double-cliquez sur une ligne pour voir le detail.")
        hint.setObjectName("subtitle")
        lay.addWidget(hint)

    def refresh(self):
        try:
            reports = self.api.list_reports(200)
        except ApiError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self._fill(reports)

    def _fill(self, reports: list):
        self.table.setRowCount(len(reports))
        for row, rep in enumerate(reports):
            values = [
                str(rep["id"]), rep["risk_level"], str(rep["risk_score"]),
                rep["sender"], rep.get("subject", ""), rep["submitted_by"],
                rep.get("submitted_at", ""),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 1:  # colonne niveau : couleur
                    item.setForeground(QColor(RISK_COLORS.get(rep["risk_level"], "#e6edf3")))
                self.table.setItem(row, col, item)

    def _open_detail(self, row: int, _col: int):
        report_id = int(self.table.item(row, 0).text())
        try:
            report = self.api.get_report(report_id)
        except ApiError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        DetailDialog(report, self).exec()


class DetailDialog(QDialog):
    def __init__(self, report: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Signalement #{report.get('id')}")
        self.setMinimumSize(560, 520)
        self.setObjectName("root")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(10)

        level = report.get("risk_level", "?")
        color = RISK_COLORS.get(level, "#8b949e")
        badge = QLabel(f"RISQUE {level.upper()}  —  score {report.get('risk_score')}/100")
        badge.setStyleSheet(
            f"background:{color}; color:#0d1117; border-radius:6px; padding:10px; font-weight:700;"
        )
        lay.addWidget(badge)

        def field(label, value):
            lay.addWidget(QLabel(f"<b>{label}</b>"))
            v = QLabel(value or "—")
            v.setWordWrap(True)
            v.setStyleSheet("color:#c9d1d9;")
            lay.addWidget(v)

        field("Expediteur", report.get("sender"))
        field("Objet", report.get("subject"))
        field("Soumis par", f"{report.get('submitted_by')}  le  {report.get('submitted_at')}")
        urls = report.get("urls") or []
        field("URLs detectees", "\n".join(urls) if urls else "aucune")

        lay.addWidget(QLabel("<b>Contenu</b>"))
        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(report.get("body", ""))
        body.setMaximumHeight(120)
        lay.addWidget(body)

        lay.addWidget(QLabel("<b>Justification du score</b>"))
        just = QTextEdit()
        just.setReadOnly(True)
        just.setPlainText((report.get("justification") or "").replace(" ; ", "\n• "))
        lay.addWidget(just, 1)

        close = QPushButton("Fermer")
        close.clicked.connect(self.accept)
        lay.addWidget(close)


# --------------------------------------------------------------------------
# Onglet : Recherche
# --------------------------------------------------------------------------
class SearchTab(QWidget):
    COLS = ["ID", "Niveau", "Score", "Expediteur", "Objet", "Par"]

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        title = QLabel("Rechercher dans les signalements")
        title.setObjectName("sectionTitle")
        lay.addWidget(title)

        bar = QGridLayout()
        bar.addWidget(QLabel("Expediteur"), 0, 0)
        self.sender = QLineEdit()
        bar.addWidget(self.sender, 0, 1)
        bar.addWidget(QLabel("Niveau"), 0, 2)
        self.level = QComboBox()
        self.level.addItems(["(tous)", "faible", "moyen", "eleve"])
        bar.addWidget(self.level, 0, 3)
        bar.addWidget(QLabel("Mot-cle"), 1, 0)
        self.keyword = QLineEdit()
        bar.addWidget(self.keyword, 1, 1)
        search_btn = QPushButton("Rechercher")
        search_btn.setObjectName("primary")
        search_btn.clicked.connect(self._search)
        bar.addWidget(search_btn, 1, 3)
        lay.addLayout(bar)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        lay.addWidget(self.table)

    def _search(self):
        level = self.level.currentText()
        if level == "(tous)":
            level = ""
        try:
            results = self.api.search_reports(
                sender=self.sender.text().strip(),
                level=level,
                keyword=self.keyword.text().strip(),
            )
        except ApiError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self.table.setRowCount(len(results))
        for row, rep in enumerate(results):
            values = [str(rep["id"]), rep["risk_level"], str(rep["risk_score"]),
                      rep["sender"], rep.get("subject", ""), rep["submitted_by"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 1:
                    item.setForeground(QColor(RISK_COLORS.get(rep["risk_level"], "#e6edf3")))
                self.table.setItem(row, col, item)


# --------------------------------------------------------------------------
# Onglet : Audit (admin uniquement)
# --------------------------------------------------------------------------
class AuditTab(QWidget):
    COLS = ["ID", "Date", "Acteur", "Action", "Resultat", "Details"]

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("Journal d'audit (administrateur)")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        refresh = QPushButton("Rafraichir")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        lay.addLayout(header)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        lay.addWidget(self.table)

    def refresh(self):
        try:
            events = self.api.list_audit(200)
        except ApiError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self.table.setRowCount(len(events))
        outcome_colors = {"success": "#3fb950", "failure": "#d29922", "denied": "#f85149"}
        for row, ev in enumerate(events):
            values = [str(ev["id"]), ev.get("timestamp", ""), ev.get("actor", ""),
                      ev["action"], ev["outcome"], ev.get("details", "")]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 4:
                    item.setForeground(QColor(outcome_colors.get(ev["outcome"], "#e6edf3")))
                self.table.setItem(row, col, item)


# --------------------------------------------------------------------------
# Fenetre principale
# --------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, api: ApiClient, app: "QApplication"):
        super().__init__()
        self.api = api
        self._app = app
        self.setWindowTitle("Plateforme anti-phishing")
        self.resize(1040, 680)

        # --- Barre du haut : info utilisateur + bouton deconnexion ---
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)

        role_label = "Administrateur" if api.is_admin() else "Analyste"
        user_info = QLabel(f"Connecte en tant que  <b>{api.login}</b>  ({role_label})")
        user_info.setStyleSheet("color: #8b949e;")
        top_layout.addWidget(user_info)
        top_layout.addStretch()

        logout_btn = QPushButton("Se deconnecter")
        logout_btn.setObjectName("danger")
        logout_btn.clicked.connect(self._logout)
        top_layout.addWidget(logout_btn)

        # --- Onglets ---
        tabs = QTabWidget()
        self.history_tab = HistoryTab(api)
        tabs.addTab(SubmitTab(api), "Soumettre")
        tabs.addTab(self.history_tab, "Historique")
        tabs.addTab(SearchTab(api), "Recherche")
        if api.is_admin():
            tabs.addTab(AuditTab(api), "Audit")
        tabs.currentChanged.connect(self._on_tab_change)
        self._tabs = tabs

        # --- Widget central : barre + onglets ---
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(top_bar)

        # Ligne separatrice
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #30363d;")
        central_layout.addWidget(sep)

        central_layout.addWidget(tabs)
        self.setCentralWidget(central)

    def _logout(self):
        confirm = QMessageBox.question(
            self, "Deconnexion",
            "Voulez-vous vraiment vous deconnecter ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            # Revocation du token cote serveur (best-effort)
            try:
                from common.http_client import post_json
                from common import config
                if self.api.token:
                    post_json(f"{config.AUTH_URL}/logout", {"token": self.api.token}, timeout=3)
            except Exception:
                pass
            self.close()
            # Rouvrir la fenetre de connexion
            _show_login(self._app)

    def _on_tab_change(self, index: int):
        widget = self._tabs.widget(index)
        if hasattr(widget, "refresh"):
            widget.refresh()


def _show_login(app: "QApplication"):
    """Affiche la fenetre de connexion. Rappelable apres deconnexion."""
    api = ApiClient()
    login_dlg = LoginDialog(api)
    if login_dlg.exec() == QDialog.Accepted:
        window = MainWindow(api, app)
        # On garde une reference pour eviter que Python detruise la fenetre.
        app._main_window = window
        window.show()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    _show_login(app)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())