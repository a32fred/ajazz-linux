from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QSpinBox, QWidget)


def label(text, role=None):
    item = QLabel(text)
    if role:
        item.setObjectName(role)
    item.setWordWrap(True)
    return item


def button(text, slot=None, primary=False):
    item = QPushButton(text)
    item.setAccessibleName(text)
    if slot:
        item.clicked.connect(slot)
    if primary:
        item.setObjectName('primary')
    return item


def combo(items, name):
    item = QComboBox()
    item.setAccessibleName(name)
    for text, data in items:
        item.addItem(text, data)
    return item


def spin(minimum, maximum, name, suffix=''):
    item = QSpinBox()
    item.setRange(minimum, maximum)
    item.setSuffix(suffix)
    item.setAccessibleName(name)
    item.setKeyboardTracking(False)
    return item


def card(title=None):
    frame = QFrame()
    frame.setObjectName('card')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(14)
    if title:
        layout.addWidget(label(title, 'heading'))
    return frame, layout


def row(*items):
    widget = QWidget()
    widget.setObjectName('row')
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    for item in items:
        layout.addWidget(item)
    return widget
