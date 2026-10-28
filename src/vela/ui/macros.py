"""Local macro library, ordered event editor and focused-only input recording."""
import copy
from pathlib import Path
import secrets
import time
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QBoxLayout, QLineEdit, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit, QFileDialog, QCheckBox)
from ..domain import Macro, MacroEvent, ValidationError
from ..formats import load_macro, save_macro
from .keys import hid_key, key_name, parse_key
from .widgets import label, card, row, button, spin, combo


class Recorder(QPlainTextEdit):
    captured = Signal(str, int, int, int)
    finished = Signal()
    unsupported = Signal(str)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.pressed = set()
        self.last_position = None
        self.setReadOnly(True)
        self.setMaximumHeight(88)
        self.setAccessibleName('Focused macro recording area')
        self.setPlainText('Start recording, then type or click inside this area. Leaving it stops recording.')

    def keyPressEvent(self, event):
        if not self.recording or not self.hasFocus():
            return super().keyPressEvent(event)
        if event.isAutoRepeat():
            return
        code = hid_key(event)
        if code is None or code == 0x67:
            self.unsupported.emit('This key has no supported HID mapping. Use the event editor for an explicit usage.')
            return
        if code not in self.pressed:
            self.pressed.add(code)
            self.captured.emit('down', code, 0, 0)
        event.accept()

    def keyReleaseEvent(self, event):
        if self.recording and not event.isAutoRepeat():
            code = hid_key(event)
            if code in self.pressed:
                self.pressed.remove(code)
                self.captured.emit('up', code, 0, 0)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def mouse_code(self, event):
        return {Qt.MouseButton.LeftButton: 0xf0, Qt.MouseButton.RightButton: 0xf1,
                Qt.MouseButton.MiddleButton: 0xf2, Qt.MouseButton.ForwardButton: 0xf3,
                Qt.MouseButton.BackButton: 0xf4}.get(event.button())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.recording and self.hasFocus():
            code = self.mouse_code(event)
            if code is not None and code not in self.pressed:
                self.pressed.add(code)
                self.captured.emit('down', code, 0, 0)
            self.last_position = event.position()

    def mouseReleaseEvent(self, event):
        if self.recording:
            code = self.mouse_code(event)
            if code in self.pressed:
                self.pressed.remove(code)
                self.captured.emit('up', code, 0, 0)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.recording and self.hasFocus() and self.last_position is not None:
            delta = event.position() - self.last_position
            dx, dy = round(delta.x()), round(delta.y())
            if dx or dy:
                self.captured.emit('move', 0, max(-128, min(127, dx)), max(-128, min(127, dy)))
            self.last_position = event.position()
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if self.recording:
            self.unsupported.emit('Wheel macro events are unavailable.')
            event.accept()
        else:
            super().wheelEvent(event)

    def focusOutEvent(self, event):
        if self.recording:
            self.finish()
        super().focusOutEvent(event)

    def finish(self):
        if not self.recording:
            return
        for code in sorted(self.pressed):
            self.captured.emit('up', code, 0, 0)
        self.pressed.clear()
        self.recording = False
        self.last_position = None
        self.finished.emit()


class MacrosPage(QWidget):
    edited = Signal()
    message = Signal(str)
    assign_requested = Signal(int, object)

    def __init__(self):
        super().__init__()
        self.library = []
        self.loading = False
        self.current_id = None
        self.last_recorded = None
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, self)
        self.columns = layout
        layout.setContentsMargins(0, 0, 0, 0)
        library, content = card('Macro library')
        self.library_panel = library
        self.library_list = QListWidget()
        self.library_list.setAccessibleName('Macro library')
        self.library_list.setMinimumHeight(40)
        content.addWidget(self.library_list, 1)
        self.library_empty = label('Create or import a macro to begin.', 'muted')
        content.addWidget(self.library_empty)
        content.addWidget(row(button('New', self.new_macro), button('Delete', self.delete_macro), stretch=True))
        content.addWidget(row(button('Import…', self.import_dialog), button('Export…', self.export_dialog), stretch=True))
        content.addWidget(label('Save workspace keeps your library on this computer.', 'muted'))
        layout.addWidget(library)
        self.editor, content = card('Sequence editor')
        self.name_edit = QLineEdit()
        self.name_edit.setAccessibleName('Macro name')
        self.name_edit.setPlaceholderText('Macro name · up to 39 UTF-16 units')
        self.loop = combo([('Counted', 'count'), ('While held', 'held'), ('Toggle', 'toggle')], 'Macro loop mode')
        self.repeat = spin(1, 250, 'Macro repeat count')
        content.addWidget(row(self.name_edit, self.loop, self.repeat))
        self.event_table = QTableWidget(0, 5)
        self.event_table.setAccessibleName('Macro events')
        self.event_table.setHorizontalHeaderLabels(['Action', 'Key / button', 'Delay (ms)', 'Move X', 'Move Y'])
        self.event_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.event_table.setMinimumHeight(140)
        content.addWidget(self.event_table, 1)
        content.addWidget(row(button('Add event', self.add_event), button('Remove', self.remove_event),
                              button('Move up', lambda: self.move_event(-1)), button('Move down', lambda: self.move_event(1)), stretch=True))
        self.count = label('0 / 70 events', 'muted')
        content.addWidget(self.count)
        content.addWidget(label('Record a sequence or enter key names such as A, Space or F1.', 'muted'))
        self.advanced = QCheckBox('Show movement columns')
        content.addWidget(self.advanced)
        self.advanced.toggled.connect(lambda on: [self.event_table.setColumnHidden(i, not on) for i in (3, 4)])
        for column in (3, 4):
            self.event_table.setColumnHidden(column, True)
        self.auto_delay = QCheckBox('Record timing')
        self.auto_delay.setChecked(True)
        self.fixed_delay = spin(0, 65535, 'Fixed recording delay', ' ms')
        self.fixed_delay.setValue(20)
        self.start_button = button('Start recording', self.start_recording)
        self.stop_button = button('Stop', self.stop_recording)
        self.stop_button.setEnabled(False)
        content.addWidget(row(self.start_button, self.stop_button, self.auto_delay, self.fixed_delay, stretch=True))
        self.recorder = Recorder()
        self.recorder.setMaximumHeight(56)
        content.addWidget(self.recorder)
        self.assign_target = combo([('Side button: Back', 3), ('Side button: Forward', 4), ('DPI button', 5)], 'Macro target button')
        self.assign_button = button('Assign to button', self.assign_current)
        content.addWidget(row(self.assign_target, self.assign_button, stretch=True))
        self.error = label('', 'error')
        content.addWidget(self.error)
        layout.addWidget(self.editor, 1)
        self.library_list.currentRowChanged.connect(self.select_macro)
        self.name_edit.textChanged.connect(self.editor_changed)
        self.loop.currentIndexChanged.connect(self.editor_changed)
        self.repeat.valueChanged.connect(self.editor_changed)
        self.auto_delay.toggled.connect(self.editor_changed)
        self.event_table.cellChanged.connect(self.editor_changed)
        self.recorder.captured.connect(self.capture_event)
        self.recorder.unsupported.connect(self.error.setText)
        self.recorder.finished.connect(self.recording_finished)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        wide = self.width() >= 700
        self.columns.setDirection(QBoxLayout.Direction.LeftToRight if wide else QBoxLayout.Direction.TopToBottom)
        self.library_panel.setMaximumWidth(240 if wide else 16777215)
        self.library_panel.setMaximumHeight(16777215 if wide else 230)
        self.library_list.setMaximumHeight(16777215 if wide else 42)

    def current(self):
        return next((macro for macro in self.library if macro.id == self.current_id), None)

    def load(self, library):
        self.stop_recording()
        self.library = library
        self.library_empty.setVisible(not library)
        self.loading = True
        self.library_list.clear()
        for macro in library:
            self.library_list.addItem(macro.name)
        index = next((i for i, m in enumerate(library) if m.id == self.current_id), 0 if library else -1)
        self.loading = False
        self.library_list.setCurrentRow(index)
        if index == -1:
            self.current_id = None
            self.editor.setEnabled(False)
        self.assign_button.setEnabled(index != -1)

    def select_macro(self, index):
        if self.loading:
            return
        self.stop_recording()
        self.current_id = self.library[index].id if 0 <= index < len(self.library) else None
        self.load_editor()

    def load_editor(self):
        macro = self.current()
        self.editor.setEnabled(macro is not None)
        if macro is None:
            return
        self.loading = True
        self.name_edit.setText(macro.name)
        self.loop.setCurrentIndex(self.loop.findData(macro.loop_mode))
        self.repeat.setValue(macro.repeat)
        self.repeat.setEnabled(macro.loop_mode == 'count')
        self.auto_delay.setChecked(macro.auto_delay)
        self.event_table.setRowCount(len(macro.events))
        for i, event in enumerate(macro.events):
            for column, value in enumerate(({'down': 'Press', 'up': 'Release', 'move': 'Move'}[event.kind],
                                            key_name(event.code) if event.kind != 'move' else '0',
                                            event.delay_ms, event.dx, event.dy)):
                self.event_table.setItem(i, column, QTableWidgetItem(str(value)))
        self.count.setText(f'{len(macro.events)} / 70 events')
        self.error.clear()
        self.loading = False

    def commit_editor(self):
        macro = self.current()
        if macro is None or self.loading:
            return
        candidate = copy.deepcopy(macro)
        candidate.name = self.name_edit.text()
        candidate.loop_mode = self.loop.currentData()
        candidate.repeat = self.repeat.value()
        candidate.auto_delay = self.auto_delay.isChecked()
        candidate.events = []
        for i in range(self.event_table.rowCount()):
            values = [self.event_table.item(i, column).text().strip() for column in range(5)]
            try:
                numbers = [parse_key(values[1])] + [int(value, 16) if value.lower().startswith(('0x', '-0x')) else int(value) for value in values[2:]]
            except ValueError as exc:
                raise ValidationError(f'Event {i + 1}: enter whole numbers for code, delay and movement.') from exc
            kind = {'Press': 'down', 'Release': 'up', 'Move': 'move'}.get(values[0], values[0])
            candidate.events.append(MacroEvent(kind, *numbers))
        candidate.validate()
        macro.__dict__.update(candidate.__dict__)
        self.repeat.setEnabled(macro.loop_mode == 'count')
        current_item = self.library_list.currentItem()
        if current_item:
            current_item.setText(macro.name)
        self.error.clear()

    def editor_changed(self, *args):
        if self.loading:
            return
        try:
            self.commit_editor()
        except ValidationError as exc:
            self.error.setText(str(exc))
        self.edited.emit()

    def new_macro(self):
        try:
            self.commit_editor()
            if len(self.library) >= 2000:
                raise ValidationError('The library already contains 2000 macros.')
        except ValidationError as exc:
            self.error.setText(str(exc))
            return
        new_id = secrets.randbelow(0xffffffff) + 1
        while any(m.id == new_id for m in self.library):
            new_id = secrets.randbelow(0xffffffff) + 1
        macro = Macro(new_id, 'New macro', [])
        self.library.append(macro)
        self.current_id = macro.id
        self.load(self.library)
        self.edited.emit()

    def delete_macro(self):
        macro = self.current()
        if macro:
            self.stop_recording()
            # Window validates references before permitting this mutation.
            self.message.emit(f'delete:{macro.id}')

    def add_event(self):
        try:
            self.commit_editor()
            macro = self.current()
            if macro is None:
                return
            if len(macro.events) >= 70:
                raise ValidationError('A macro supports at most 70 events.')
            macro.events.append(MacroEvent('down', 4))
            self.load_editor()
            self.event_table.setCurrentCell(len(macro.events) - 1, 0)
            self.edited.emit()
        except ValidationError as exc:
            self.error.setText(str(exc))

    def remove_event(self):
        macro = self.current()
        index = self.event_table.currentRow()
        if macro and 0 <= index < len(macro.events):
            del macro.events[index]
            self.load_editor()
            self.edited.emit()

    def move_event(self, offset):
        try:
            self.commit_editor()
        except ValidationError as exc:
            self.error.setText(str(exc))
            return
        macro = self.current()
        index = self.event_table.currentRow()
        if macro and 0 <= index + offset < len(macro.events):
            macro.events[index], macro.events[index + offset] = macro.events[index + offset], macro.events[index]
            self.load_editor()
            self.event_table.setCurrentCell(index + offset, 0)
            self.edited.emit()

    def start_recording(self):
        if not self.current():
            self.new_macro()
        try:
            self.commit_editor()
        except ValidationError as exc:
            self.error.setText(str(exc))
            return
        if not self.current():
            return
        self.last_recorded = None
        self.recorder.recording = True
        self.recorder.setFocus()
        self.recorder.setPlainText('Recording here only. Press Stop or leave this area to finish.')
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def assign_current(self):
        try:
            self.commit_editor()
            macro = self.current()
            if macro is None or not macro.events:
                raise ValidationError('Record or add a sequence before assigning it.')
            self.assign_requested.emit(self.assign_target.currentData(), macro.id)
        except ValidationError as exc:
            self.error.setText(str(exc))

    def stop_recording(self):
        self.recorder.finish()

    def recording_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.recorder.setPlainText('Recording stopped. Review the sequence before applying.')

    def capture_event(self, kind, code, dx, dy):
        macro = self.current()
        if macro is None:
            return
        # Reserve releases for held inputs so a full recording never gets stuck.
        if len(macro.events) + len(self.recorder.pressed) >= 70 and kind != 'up':
            if kind == 'down':
                self.recorder.pressed.discard(code)  # this press was never appended
            self.recorder.finish()
            self.error.setText('70-event limit reached. Recording stopped; review the final releases.')
            return
        if len(macro.events) >= 70:
            return
        now = time.monotonic()
        if macro.events and self.last_recorded is not None:
            macro.events[-1].delay_ms = min(65535, round((now - self.last_recorded) * 1000)) if macro.auto_delay else self.fixed_delay.value()
        macro.events.append(MacroEvent(kind, code, 0, dx, dy))
        self.last_recorded = now
        self.load_editor()
        self.edited.emit()

    def import_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import macro', '', 'Legacy macro (*.jmm)')
        if path:
            try:
                self.commit_editor()
                macro = load_macro(Path(path))
                if any(m.id == macro.id for m in self.library):
                    macro.id = max([m.id for m in self.library] + [0]) + 1
                if macro.id > 0xffffffff or len(self.library) >= 2000:
                    raise ValidationError('No room for another macro in this library.')
                self.library.append(macro)
                self.current_id = macro.id
                self.load(self.library)
                self.edited.emit()
            except (OSError, ValueError, ValidationError) as exc:
                self.error.setText(str(exc))
            except Exception as exc:
                self.error.setText(f'Could not import macro: {exc}')

    def export_dialog(self):
        if not self.current():
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Export macro', 'macro.jmm', 'Legacy macro (*.jmm)')
        if path:
            try:
                self.commit_editor()
                save_macro(Path(path), self.current())
                self.message.emit('Macro exported.')
            except Exception as exc:
                self.error.setText(f'Could not export macro: {exc}. Use a native workspace backup to retain all fields.')
