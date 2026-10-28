from PySide6.QtCore import Qt, QRegularExpression, QTimer, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QLineEdit, QSizePolicy, QWidget)


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


class _Field(QLineEdit):
    """Select everything on focus so a typed number replaces the old one."""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        had_focus = self.hasFocus()
        super().mousePressEvent(event)
        if not had_focus:
            QTimer.singleShot(0, self.selectAll)


class Stepper(QWidget):
    """Number input: large minus/plus buttons that repeat while held, and a field to type into.

    Up/Down step by one, PageUp/PageDown by ten; the wheel steps only while the field has focus.
    """
    valueChanged = Signal(int)

    def __init__(self, minimum, maximum, name, suffix=''):
        super().__init__()
        self._min, self._max, self._step, self._value = minimum, maximum, 1, minimum
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.down = self._step_button('\u2212', f'{name}: decrease', -1)
        self.field = _Field()
        self.field.setObjectName('stepfield')
        self.field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.field.setValidator(QRegularExpressionValidator(QRegularExpression(r'\d{0,6}'), self))
        self.field.setAccessibleName(name)
        self.field.setFixedSize(max(64, 12 + 9 * len(str(maximum))), 34)
        self.field.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.field.editingFinished.connect(self._commit)
        self.up = self._step_button('+', f'{name}: increase', 1)
        layout.addWidget(self.down)
        layout.addWidget(self.field)
        layout.addWidget(self.up)
        self.unit = QLabel(suffix.strip())
        self.unit.setObjectName('unit')
        layout.addWidget(self.unit)
        self.unit.setVisible(bool(suffix.strip()))
        self.setFocusProxy(self.field)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(name)
        self.field.installEventFilter(self)
        self._show()

    def _step_button(self, text, name, direction):
        item = QPushButton(text)
        item.setObjectName('step')
        item.setAccessibleName(name)
        item.setFixedSize(34, 34)
        item.setAutoRepeat(True)
        item.setAutoRepeatDelay(400)
        item.setAutoRepeatInterval(70)
        item.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        item.clicked.connect(lambda: self.setValue(self._value + direction * self._step))
        return item

    def eventFilter(self, source, event):
        if source is self.field and self.isEnabled():
            if event.type() == event.Type.KeyPress:
                key = event.key()
                jump = {Qt.Key.Key_Up: 1, Qt.Key.Key_Down: -1, Qt.Key.Key_PageUp: 10, Qt.Key.Key_PageDown: -10}.get(key)
                if jump:
                    self.setValue(self._value + jump * self._step)
                    return True
                if key == Qt.Key.Key_Escape:
                    self._show()
                    return True
            elif event.type() == event.Type.Wheel:
                if self.field.hasFocus():
                    self.setValue(self._value + (1 if event.angleDelta().y() > 0 else -1) * self._step)
                event.accept()
                return True
        return super().eventFilter(source, event)

    def _show(self):
        self.field.setText(str(self._value))
        self.down.setEnabled(self.isEnabled() and self._value > self._min)
        self.up.setEnabled(self.isEnabled() and self._value < self._max)

    def _commit(self):
        text = self.field.text().strip()
        self.setValue(int(text)) if text.lstrip('-').isdigit() else self._show()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.Type.EnabledChange:
            self._show()

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(self._min, min(self._max, int(value)))
        changed = value != self._value
        self._value = value
        self._show()
        if changed:
            self.valueChanged.emit(value)

    def setRange(self, minimum, maximum):
        self._min, self._max = minimum, maximum
        self.setValue(self._value)

    def setSingleStep(self, step):
        self._step = step

    def setKeyboardTracking(self, _enabled):
        pass


def spin(minimum, maximum, name, suffix=''):
    return Stepper(minimum, maximum, name, suffix)


def card(title=None):
    frame = QFrame()
    frame.setObjectName('card')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(10)
    if title:
        layout.addWidget(label(title, 'heading'))
    return frame, layout


def row(*items, stretch=False):
    widget = QWidget()
    widget.setObjectName('row')
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for item in items:
        layout.addWidget(item)
    if stretch:
        layout.addStretch()
    return widget
