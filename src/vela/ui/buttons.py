import copy
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDialog, QDialogButtonBox, QLineEdit, QCheckBox)
from ..domain import Binding, ValidationError
from ..protocol import DIRECT_ACTIONS, CONSUMER_USAGES, encode_combination
from .keys import hid_key, key_name
from .widgets import card, button, label, combo


def binding_text(binding, macros):
    if binding.action == 'macro':
        macro = next((m for m in macros if m.id == binding.macro_id), None)
        return 'Macro · ' + (macro.name if macro else 'Unavailable')
    if binding.action == 'keyboard':
        mods = [name for mask, name in ((1, 'Ctrl'), (2, 'Shift'), (4, 'Alt'), (8, 'Super')) if binding.modifiers & mask]
        return ' + '.join(mods + [key_name(key) for key in binding.keys]) or 'Keyboard combination'
    if binding.action.startswith('consumer:'):
        return next((name for name, usage in CONSUMER_USAGES.items() if binding.action == f'consumer:{usage:04x}'), binding.action)
    if binding.action.startswith(('unknown:', 'legacy:')):
        return 'Preserved device / imported assignment'
    return binding.action.replace('_', ' ').capitalize()


class MouseDiagram(QWidget):
    selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(160, 250)
        self.setAccessibleName('Mouse diagram. Buttons: 1 left, 2 right, 3 wheel, 4 back, 5 forward, 6 DPI.')
        self.controls = []
        for index, name in enumerate(('Left click', 'Right click', 'Wheel click', 'Back', 'Forward', 'DPI button')):
            control = button(str(index + 1), lambda checked=False, i=index: self.selected.emit(i))
            control.setParent(self)
            control.setAccessibleName(f'Assign {name} on mouse diagram')
            control.setToolTip(f'{name}: choose assignment')
            control.setCursor(Qt.CursorShape.PointingHandCursor)
            control.setStyleSheet('QPushButton { background: transparent; border: 1px solid transparent; padding: 0; min-height: 0; } '
                                  'QPushButton:hover, QPushButton:focus { background: #143A34; border: 1px solid #3CCFB0; }')
            self.controls.append(control)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        x, y = self.width() // 2 - 80, self.height() // 2 - 120
        for control, (left, top, width, height) in zip(self.controls, (
                (28, 15, 40, 70), (94, 15, 40, 70), (68, 28, 24, 38),
                (12, 135, 28, 26), (12, 105, 28, 26), (68, 109, 24, 28))):
            control.setGeometry(x + left, y + top, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2 - 80, self.height() / 2 - 120)
        painter.setPen(QPen(QColor('#52666F'), 2))
        painter.setBrush(QColor('#27343B'))
        painter.drawRoundedRect(QRectF(12, 4, 136, 232), 65, 65)
        painter.drawLine(80, 5, 80, 95)
        painter.drawLine(15, 95, 145, 95)
        painter.setPen(QPen(QColor('#52666F'), 2))
        painter.drawRoundedRect(QRectF(70, 28, 20, 38), 8, 8)
        painter.drawRoundedRect(QRectF(73, 113, 14, 20), 5, 5)


class KeyCapture(QLineEdit):
    def __init__(self):
        super().__init__()
        self.keys = []
        self.modifiers = 0
        self.pressed = set()
        self.setReadOnly(True)
        self.setPlaceholderText('Focus here and press a combination')
        self.setAccessibleName('Capture keyboard combination')

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        code = hid_key(event)
        if code is None:
            self.setText('Unsupported key — choose a standard keyboard key')
            return
        if code < 0xe0 and not any(key < 0xe0 for key in self.pressed):
            self.keys = []
        self.pressed.add(code)
        mods = event.modifiers()
        self.modifiers = sum(mask for qt, mask in ((Qt.KeyboardModifier.ControlModifier, 1),
            (Qt.KeyboardModifier.ShiftModifier, 2), (Qt.KeyboardModifier.AltModifier, 4),
            (Qt.KeyboardModifier.MetaModifier, 8)) if mods & qt)
        if code < 0xe0 and code not in self.keys:
            self.keys.append(code)
        self.setText(binding_text(Binding('keyboard', self.keys, self.modifiers), []))

    def keyReleaseEvent(self, event):
        self.pressed.discard(hid_key(event))
        event.accept()

    def focusOutEvent(self, event):
        self.pressed.clear()
        super().focusOutEvent(event)


class BindingDialog(QDialog):
    def __init__(self, binding, macros, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Assign button')
        self.resize(450, 320)
        self.original = copy.deepcopy(binding)
        layout = QVBoxLayout(self)
        actions = [(action.replace('_', ' ').capitalize(), action) for action in DIRECT_ACTIONS]
        actions += [('Keyboard combination', 'keyboard'), ('Macro', 'macro')]
        actions += [(name, f'consumer:{usage:04x}') for name, usage in CONSUMER_USAGES.items()]
        if binding.action.startswith(('unknown:', 'legacy:')):
            actions.insert(0, ('Keep current assignment', binding.action))
        self.action = combo(actions, 'Button action')
        self.action.setCurrentIndex(self.action.findData(binding.action))
        layout.addWidget(self.action)
        self.capture = KeyCapture()
        self.capture.keys = list(binding.keys)
        self.capture.modifiers = binding.modifiers
        self.capture.setText(binding_text(binding, macros) if binding.action == 'keyboard' else '')
        layout.addWidget(self.capture)
        self.clear = button('Clear combination', self.clear_keys)
        layout.addWidget(self.clear)
        self.modifiers = []
        mods = QHBoxLayout()
        for bit, title in ((1, 'Ctrl'), (2, 'Shift'), (4, 'Alt'), (8, 'Super')):
            control = QCheckBox(title)
            control.setChecked(bool(binding.modifiers & bit))
            mods.addWidget(control)
            self.modifiers.append((bit, control))
        layout.addLayout(mods)
        self.macro = combo([(m.name, m.id) for m in macros], 'Assigned macro')
        self.macro.setCurrentIndex(max(0, self.macro.findData(binding.macro_id)))
        layout.addWidget(self.macro)
        self.help = label('', 'muted')
        layout.addWidget(self.help)
        self.error = label('', 'error')
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept_validated)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.action.currentIndexChanged.connect(self.update_controls)
        self.update_controls()
        self.capture.textChanged.connect(self.sync_modifiers)

    def sync_modifiers(self):
        for bit, control in self.modifiers:
            control.setChecked(bool(self.capture.modifiers & bit))

    def clear_keys(self):
        self.capture.keys, self.capture.modifiers = [], 0
        self.capture.clear()
        self.sync_modifiers()

    def update_controls(self):
        keyboard = self.action.currentData() == 'keyboard'
        self.capture.setEnabled(keyboard)
        self.clear.setEnabled(keyboard)
        self.capture.setVisible(keyboard)
        self.clear.setVisible(keyboard)
        for _, control in self.modifiers:
            control.setEnabled(keyboard)
            control.setVisible(keyboard)
        macro = self.action.currentData() == 'macro'
        self.macro.setEnabled(macro)
        self.macro.setVisible(macro)
        self.help.setText('Press the shortcut together. A new shortcut replaces the previous capture. '
                          'Maximum 3 keys and 5 keys + modifiers.' if keyboard else
                          'Choose a macro created on the Macros page.' if macro else
                          'Confirm this assignment, then click Apply to mouse.')

    def accept_validated(self):
        action = self.action.currentData()
        binding = Binding(action)
        if action == 'keyboard':
            binding.keys = list(self.capture.keys)
            binding.modifiers = sum(bit for bit, control in self.modifiers if control.isChecked())
        elif action == 'macro':
            binding.macro_id = self.macro.currentData()
            if binding.macro_id is None:
                self.error.setText('Create or import a macro first.')
                return
        elif action == self.original.action and action.startswith(('unknown:', 'legacy:')):
            binding = self.original
        try:
            binding.validate()
            if action == 'keyboard' or action.startswith('consumer:'):
                encode_combination(binding)
        except ValidationError as exc:
            self.error.setText(str(exc))
            return
        self.binding = binding
        self.accept()


class ButtonsPage(QWidget):
    edited = Signal()

    def __init__(self):
        super().__init__()
        self.settings, self.macros = None, []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        frame, content = card('Button assignments')
        content.addWidget(label('Click a numbered button on the mouse or choose its assignment below. Apply to mouse confirms your changes.', 'muted'))
        body = QHBoxLayout()
        self.diagram = MouseDiagram()
        self.diagram.selected.connect(self.edit_binding)
        body.addWidget(self.diagram, 1)
        assignments = QFormLayout()
        assignments.setSpacing(10)
        self.assignments = []
        for index, name in enumerate(('Left click', 'Right click', 'Wheel click', 'Back', 'Forward', 'DPI button')):
            item = button('', lambda checked=False, i=index: self.edit_binding(i))
            item.setStyleSheet('QPushButton { text-align: left; padding-left: 12px; }')
            item.setFixedWidth(240)
            item.setAccessibleName(f'Assign {name}')
            assignments.addRow(f'{index + 1}  {name}', item)
            self.assignments.append(item)
        body.addLayout(assignments, 3)
        body.addStretch(2)
        content.addLayout(body)
        layout.addWidget(frame)
        layout.addWidget(label('Keep a reachable left-click assignment when changing buttons. Macro playback is performed by the mouse after Apply.', 'muted'))
        layout.addStretch()

    def load(self, settings, macros):
        self.settings, self.macros = settings, macros
        for binding, item in zip(settings.bindings, self.assignments):
            item.setText(binding_text(binding, macros))

    def edit_binding(self, index):
        dialog = BindingDialog(self.settings.bindings[index], self.macros, self)
        if dialog.exec():
            self.settings.bindings[index] = dialog.binding
            self.load(self.settings, self.macros)
            self.edited.emit()
