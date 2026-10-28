"""Ink-dark surfaces with one accent, the teal of the sail logo, marking only the active or primary state."""
from pathlib import Path
from string import Template

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QProxyStyle, QStyle


BG, PANEL, RAISED, FIELD = '#0F1417', '#171E22', '#1E282D', '#27343B'
BORDER, BORDER_STRONG = '#34454D', '#52666F'
TEXT, MUTED, DISABLED = '#E8EEEC', '#9BAEA8', '#62736E'
ACCENT, ACCENT_TEXT, ACCENT_DIM = '#3CCFB0', '#04201B', '#143A34'
WARN, ERROR = '#E9B866', '#FF8F85'


class VelaStyle(QProxyStyle):
    """Keep native control geometry while drawing legible indicators."""

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            checked = bool(option.state & QStyle.StateFlag.State_On)
            enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
            bounds = option.rect.adjusted(1, 1, -1, -1)
            painter.setPen(QPen(QColor(ACCENT if checked and enabled else BORDER_STRONG), 1))
            painter.setBrush(QColor(ACCENT if checked and enabled else FIELD))
            painter.drawRoundedRect(bounds, 3, 3)
            if checked:
                painter.setPen(QPen(QColor(ACCENT_TEXT if enabled else DISABLED), 2,
                                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPolyline(QPolygonF([QPointF(bounds.left() + bounds.width() * .2, bounds.center().y()),
                                               QPointF(bounds.left() + bounds.width() * .43, bounds.bottom() - bounds.height() * .25),
                                               QPointF(bounds.right() - bounds.width() * .17, bounds.top() + bounds.height() * .25)]))
            painter.restore()
            return
        if element in (QStyle.PrimitiveElement.PE_IndicatorArrowUp, QStyle.PrimitiveElement.PE_IndicatorArrowDown):
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(TEXT if option.state & QStyle.StateFlag.State_Enabled else DISABLED), 1.5))
            center = option.rect.center()
            direction = -1 if element == QStyle.PrimitiveElement.PE_IndicatorArrowUp else 1
            painter.drawPolyline(QPolygonF([QPointF(center.x() - 3, center.y() - direction),
                                           QPointF(center.x(), center.y() + direction * 2),
                                           QPointF(center.x() + 3, center.y() - direction)]))
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


STYLE = Template('''
QWidget { background: $BG; color: $TEXT; font-size: 13px; }
QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget { background: $BG; }
QFrame#topbar { background: $PANEL; border-bottom: 1px solid $BORDER; }
QFrame#device { background: $PANEL; border: 1px solid $BORDER; border-radius: 6px; }
QFrame#device QLabel, QFrame#device QWidget#row { background: transparent; }
QFrame#card { background: $PANEL; border: 1px solid $BORDER; border-radius: 6px; }
QFrame#card QLabel, QFrame#card QCheckBox { background: transparent; }
QWidget#row { background: transparent; }
QLabel#title { font-size: 20px; font-weight: 600; }
QLabel#heading { font-size: 15px; font-weight: 600; background: transparent; }
QLabel#large { font-size: 46px; font-weight: 700; color: $ACCENT; background: transparent; }
QLabel#unit { font-size: 13px; color: $MUTED; background: transparent; }
QLabel#muted { color: $MUTED; background: transparent; }
QLabel#badge { color: $WARN; background: transparent; border: 1px solid $WARN; border-radius: 3px; padding: 3px 7px; font-size: 11px; font-weight: 600; }
QLabel#error { color: $ERROR; background: transparent; }
QPushButton { background: $RAISED; border: 1px solid $BORDER_STRONG; border-radius: 4px; padding: 6px 12px; min-height: 18px; }
QPushButton:hover { background: #2A373D; border-color: $MUTED; }
QPushButton:pressed { background: $ACCENT_DIM; }
QPushButton#primary { background: $ACCENT; color: $ACCENT_TEXT; font-weight: 700; border-color: $ACCENT; }
QPushButton#primary:hover { background: #63E0C6; }
QPushButton:checked { background: $ACCENT_DIM; color: $ACCENT; font-weight: 600; border-color: $ACCENT; }
QPushButton:disabled, QPushButton#primary:disabled { color: $DISABLED; background: $PANEL; border-color: $BORDER; }
QPushButton:focus, QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTableWidget:focus, QPlainTextEdit:focus { border: 1px solid $ACCENT; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit { background: $FIELD; border: 1px solid $BORDER_STRONG; border-radius: 4px; padding: 5px 7px; selection-background-color: $ACCENT; selection-color: $ACCENT_TEXT; }
QPushButton#step { padding: 0; min-height: 0; font-size: 18px; font-weight: 600; }
QPushButton#step:disabled { color: $DISABLED; }
QLineEdit#stepfield { font-size: 14px; padding: 0 4px; }
QComboBox { min-height: 20px; }
QComboBox::drop-down { width: 22px; border: none; }
QComboBox::down-arrow { image: url($ASSETS/spin-down.svg); width: 10px; height: 8px; }
QSpinBox { padding-right: 22px; }
QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; width: 20px; background: $RAISED; border-left: 1px solid $BORDER_STRONG; }
QSpinBox::up-button { subcontrol-position: top right; border-top-right-radius: 4px; }
QSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 4px; border-top: 1px solid $BORDER; }
QSpinBox::up-arrow { image: url($ASSETS/spin-up.svg); width: 10px; height: 8px; }
QSpinBox::down-arrow { image: url($ASSETS/spin-down.svg); width: 10px; height: 8px; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: $ACCENT_DIM; }
QComboBox QAbstractItemView { background: $RAISED; border: 1px solid $BORDER_STRONG; selection-background-color: $ACCENT_DIM; selection-color: $ACCENT; }
QSpinBox:disabled, QComboBox:disabled, QLineEdit:disabled, QPlainTextEdit:disabled { color: $DISABLED; background: $PANEL; border-color: $BORDER; }
QListWidget { background: $FIELD; border: 1px solid $BORDER; border-radius: 4px; outline: none; }
QListWidget::item { padding: 9px 10px; }
QListWidget::item:selected { background: $ACCENT_DIM; color: $ACCENT; }
QListWidget::item:focus { border: 1px solid $ACCENT; }
QListWidget#navigation { background: transparent; border: none; }
QListWidget#navigation::item { padding: 9px 14px; border-bottom: 2px solid transparent; color: $MUTED; }
QListWidget#navigation::item:hover { color: $TEXT; }
QListWidget#navigation::item:selected { background: transparent; color: $ACCENT; border-bottom: 2px solid $ACCENT; font-weight: 600; }
QTableWidget { background: $FIELD; border: 1px solid $BORDER; border-radius: 4px; gridline-color: $BORDER; selection-background-color: $ACCENT_DIM; selection-color: $ACCENT; }
QTableWidget QTableCornerButton::section, QHeaderView::section { background: $RAISED; color: $MUTED; border: none; border-bottom: 1px solid $BORDER; padding: 6px; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 4px; border-radius: 2px; background: $BORDER_STRONG; }
QSlider::sub-page:horizontal { height: 4px; border-radius: 2px; background: $ACCENT; }
QSlider::handle:horizontal { background: $TEXT; border: 3px solid $ACCENT; width: 12px; height: 12px; margin: -8px 0; border-radius: 9px; }
QScrollBar:vertical { background: $BG; width: 10px; }
QScrollBar::handle:vertical { background: $BORDER_STRONG; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QToolTip { color: $TEXT; background: $RAISED; border: 1px solid $BORDER_STRONG; }
''').substitute(globals(), ASSETS=(Path(__file__).parents[1] / 'assets').as_posix())
