"""Original Vela palette, with system fonts and visible keyboard focus."""
STYLE = '''
QWidget { background: #0B1220; color: #E9F1FA; font-size: 14px; }
QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget { background: #0B1220; }
QFrame#sidebar { background: #0E1726; border-right: 1px solid #26354B; }
QFrame#card { background: #121D2E; border: 1px solid #26354B; border-radius: 12px; }
QFrame#card QLabel, QFrame#card QCheckBox { background: transparent; }
QWidget#row { background: transparent; }
QLabel#title { font-size: 28px; font-weight: 600; }
QLabel#heading { font-size: 16px; font-weight: 600; background: transparent; }
QLabel#large { font-size: 40px; font-weight: 600; color: #4DE0BA; }
QLabel#muted { color: #91A4B8; background: transparent; }
QLabel#badge { color: #F2B66D; border: 1px solid #765D42; border-radius: 8px; padding: 7px; }
QLabel#error { color: #F08080; background: transparent; }
QPushButton { background: #18263A; border: 1px solid #26354B; border-radius: 7px; padding: 8px 12px; }
QPushButton:hover { border-color: #91A4B8; }
QPushButton:pressed { background: #26354B; }
QPushButton#primary, QPushButton:checked { background: #4DE0BA; color: #0B1220; font-weight: 600; border-color: #4DE0BA; }
QPushButton:disabled { color: #64758C; background: #121D2E; border-color: #26354B; }
QPushButton:focus, QComboBox:focus, QSpinBox:focus, QLineEdit:focus, QTableWidget:focus, QPlainTextEdit:focus { border: 2px solid #4DE0BA; }
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { background: #18263A; border: 1px solid #26354B; border-radius: 6px; padding: 6px; selection-background-color: #4DE0BA; selection-color: #0B1220; }
QComboBox QAbstractItemView { background: #18263A; selection-background-color: #26354B; }
QSpinBox:disabled, QComboBox:disabled, QLineEdit:disabled { color: #64758C; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 12px 10px; border-radius: 7px; }
QListWidget::item:selected { background: #18263A; color: #4DE0BA; border-left: 3px solid #4DE0BA; }
QListWidget::item:focus { border: 1px solid #4DE0BA; }
QTableWidget { background: #121D2E; border: 1px solid #26354B; gridline-color: #26354B; selection-background-color: #26354B; }
QTableWidget QTableCornerButton::section, QHeaderView::section { background: #18263A; color: #91A4B8; border: none; padding: 6px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #91A4B8; border-radius: 4px; background: #18263A; }
QCheckBox::indicator:checked { background: #4DE0BA; border-color: #4DE0BA; image: none; }
QSlider::groove:horizontal { height: 5px; border-radius: 2px; background: #26354B; }
QSlider::handle:horizontal { background: #4DE0BA; width: 16px; margin: -6px 0; border-radius: 8px; }
QScrollBar:vertical { background: #0B1220; width: 10px; }
QScrollBar::handle:vertical { background: #26354B; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QToolTip { color: #E9F1FA; background: #18263A; border: 1px solid #4DE0BA; }
'''
