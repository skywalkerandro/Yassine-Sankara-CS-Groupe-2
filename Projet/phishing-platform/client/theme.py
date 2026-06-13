"""
Theme visuel (QSS) de l'application. Palette sombre, sobre et lisible,
avec des couleurs semantiques pour les niveaux de risque.
"""

# Couleurs des niveaux de risque (reutilisees dans le code).
RISK_COLORS = {
    "faible": "#3fb950",   # vert
    "moyen": "#d29922",    # orange
    "eleve": "#f85149",    # rouge
}

STYLESHEET = """
* {
    font-family: -apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 14px;
    color: #e6edf3;
}
QMainWindow, QWidget#root, QDialog {
    background-color: #0d1117;
}
QLabel#title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#subtitle {
    font-size: 13px;
    color: #8b949e;
}
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #1f6feb;
}
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover { background-color: #30363d; }
QPushButton:pressed { background-color: #161b22; }
QPushButton#primary {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
}
QPushButton#primary:hover { background-color: #2ea043; }
QPushButton#danger {
    background-color: #21262d;
    border: 1px solid #30363d;
}
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    padding: 10px 18px;
    border-bottom: 2px solid transparent;
    color: #8b949e;
}
QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid #1f6feb;
}
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
}
QHeaderView::section {
    background-color: #161b22;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background-color: #1f6feb; }
QStatusBar { color: #8b949e; }
QScrollBar:vertical { background: #0d1117; width: 10px; }
QScrollBar::handle:vertical { background: #30363d; border-radius: 5px; }
"""
