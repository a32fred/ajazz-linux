"""Native desktop shell. Local profiles are drafts, not assumed hardware banks."""
import copy
from pathlib import Path
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QScrollArea, QComboBox, QFileDialog, QInputDialog,
    QMessageBox, QSizePolicy)

from ..domain import ApplyError, ValidationError, default_workspace
from ..formats import load_profile, save_profile, load_dct, select_profile_macros
from ..protocol import encode_macro
from ..service import MouseService
from ..storage import ProfileStore
from .worker import HardwareWorker
from .settings_pages import SensitivityPage, LightingPage
from .buttons import ButtonsPage
from .macros import MacrosPage
from .theme import STYLE
from .widgets import label, button, row


class MainWindow(QMainWindow):
    requested = Signal(str, object)
    stopping = Signal()

    def __init__(self, *, service=None, store=None, demo=False):
        super().__init__()
        self.demo = demo
        self.store = store or ProfileStore()
        self.snapshot = None
        self._snapshot_macros = []
        self.busy = False
        self.closing = False
        self.thread_stopped = False
        self.loading = False
        self.macros_dirty = False
        self.dirty = False
        self.devices = []
        self.load_error = None
        self._startup_autoconnect = demo
        self._saved_draft_loaded = self.store.path.exists()
        self._preserve_connect_draft = False
        self._device_macro_aliases = {}
        self._pending_local_macro_ids = set()
        try:
            self.workspace = self.store.load()
        except Exception as exc:
            # Existing invalid files remain intact until the user chooses a new destination.
            self.workspace = default_workspace()
            self.load_error = str(exc)
        self.draft = copy.deepcopy(self.workspace.profiles[self.workspace.selected_profile].settings)
        self.setWindowTitle('Vela Mouse Studio' + (' — Demo' if demo else ''))
        self.setWindowIcon(QIcon(str(Path(__file__).parents[1] / 'assets' / 'vela.svg')))
        self.resize(1100, 800)
        self.setMinimumSize(800, 580)
        self.setStyleSheet(STYLE)
        self.build_shell()
        self.service = service or MouseService(demo=demo)
        self.io_thread = QThread(self)
        self.worker = HardwareWorker(self.service)
        self.worker.moveToThread(self.io_thread)
        self.requested.connect(self.worker.execute)
        self.stopping.connect(self.worker.shutdown)
        self.worker.completed.connect(self.operation_finished)
        self.worker.stopped.connect(self.io_thread.quit)
        self.io_thread.finished.connect(self.worker.deleteLater)
        self.io_thread.finished.connect(self.thread_finished)
        self.io_thread.start()
        self.load_pages()
        self.update_profiles()
        self.update_actions()
        if self.load_error:
            self.set_status(f'Workspace could not be loaded. Original file preserved: {self.load_error}. Import a valid backup or choose another workspace directory.', error=True)
        elif demo:
            QTimer.singleShot(0, self.scan_devices)
        else:
            self.set_status('Select Scan to find a mouse. Draft edits are local until Apply.')

    def build_shell(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(180)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 20)
        side.setSpacing(18)
        brand = QHBoxLayout()
        logo = QSvgWidget(str(Path(__file__).parents[1] / 'assets' / 'vela.svg'))
        logo.setFixedSize(38, 42)
        logo.setAccessibleName('Vela sail logo')
        brand.addWidget(logo)
        wordmark = QVBoxLayout()
        wordmark.setSpacing(2)
        wordmark.addWidget(label('Vela', 'heading'))
        subtitle = label('MOUSE STUDIO', 'muted')
        subtitle.setStyleSheet('font-size: 10px; color: #91A4B8;')
        wordmark.addWidget(subtitle)
        brand.addLayout(wordmark)
        side.addLayout(brand)
        self.navigation = QListWidget()
        self.navigation.setAccessibleName('Pages')
        self.navigation.addItems(['Sensitivity', 'Buttons', 'Lighting', 'Macros'])
        side.addWidget(self.navigation)
        side.addWidget(button('About Vela', self.show_about))
        side.addWidget(label('Linux · Windows\nv0.1.0', 'muted'))
        shell.addWidget(sidebar)
        main = QWidget()
        content = QVBoxLayout(main)
        content.setContentsMargins(24, 20, 24, 16)
        content.setSpacing(14)
        self.page_title = label('Sensitivity', 'title')
        self.mode_badge = label('DEMO MODE' if self.demo else 'REAL DEVICE', 'badge')
        self.mode_badge.setMaximumWidth(135)
        content.addWidget(row(self.page_title, self.mode_badge))
        self.device_summary = label('No mouse connected', 'muted')
        content.addWidget(self.device_summary)
        self.connection_bar = QWidget()
        connections = QHBoxLayout(self.connection_bar)
        connections.setContentsMargins(0, 0, 0, 0)
        self.device_picker = QComboBox()
        self.device_picker.setAccessibleName('Available mice')
        self.device_picker.setMinimumContentsLength(13)
        self.device_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.scan_button = button('Scan', self.scan_devices)
        self.connect_button = button('Read mouse', self.connect_device)
        self.refresh_button = button('Refresh', self.refresh_device)
        connections.addWidget(self.device_picker, 1)
        connections.addWidget(self.scan_button)
        connections.addWidget(self.connect_button)
        connections.addWidget(self.refresh_button)
        content.addWidget(self.connection_bar)
        self.profile_bar = QWidget()
        profiles = QHBoxLayout(self.profile_bar)
        profiles.setContentsMargins(0, 0, 0, 0)
        profiles.addWidget(label('Local profile', 'muted'))
        self.profile_picker = QComboBox()
        self.profile_picker.setAccessibleName('Local draft profile')
        profiles.addWidget(self.profile_picker, 1)
        profiles.addWidget(button('Rename', self.rename_profile))
        profiles.addWidget(button('Save workspace', self.save_workspace))
        content.addWidget(self.profile_bar)
        self.sensitivity = SensitivityPage()
        self.buttons = ButtonsPage()
        self.lighting = LightingPage()
        self.macros = MacrosPage()
        self.pages = QStackedWidget()
        for page in (self.sensitivity, self.buttons, self.lighting, self.macros):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
            page.edited.connect(self.draft_changed)
        self.macros.edited.connect(self.macro_changed)
        self.macros.message.connect(self.macro_message)
        content.addWidget(self.pages, 1)
        self.files_bar = row(button('Import…', self.import_dialog), button('Export…', self.export_dialog))
        content.addWidget(self.files_bar)
        self.status = label('', 'muted')
        self.status.setAccessibleName('Operation status')
        self.status.setMinimumHeight(38)
        content.addWidget(self.status)
        self.reset_button = button('Reset draft', self.reset_draft)
        self.apply_button = button('Apply to mouse', self.apply_draft, primary=True)
        footer = QHBoxLayout()
        self.draft_status = label('Draft is local', 'muted')
        footer.addWidget(self.draft_status, 1)
        footer.addWidget(self.reset_button)
        footer.addWidget(self.apply_button)
        content.addLayout(footer)
        shell.addWidget(main, 1)
        self.navigation.currentRowChanged.connect(self.change_page)
        self.navigation.setCurrentRow(0)
        self.profile_picker.currentIndexChanged.connect(self.change_profile)

    def change_page(self, index):
        self.macros.stop_recording()
        self.pages.setCurrentIndex(index)
        self.page_title.setText(('Sensitivity', 'Buttons', 'Lighting', 'Macros')[index])
        if index == 1:
            self.buttons.load(self.draft, self.workspace.macros)

    def load_pages(self):
        self.sensitivity.load(self.draft)
        self.buttons.load(self.draft, self.workspace.macros)
        self.lighting.load(self.draft)
        self.macros.load(self.workspace.macros)

    def update_profiles(self):
        self.loading = True
        self.profile_picker.clear()
        for index, profile in enumerate(self.workspace.profiles):
            self.profile_picker.addItem(f'{index + 1} · {profile.name}', index)
        self.profile_picker.setCurrentIndex(self.workspace.selected_profile)
        self.loading = False

    def staged_workspace(self):
        self.macros.commit_editor()
        candidate = copy.deepcopy(self.workspace)
        candidate.profiles[candidate.selected_profile].settings = copy.deepcopy(self.draft)
        candidate.validate()
        return candidate

    def change_profile(self, index):
        if self.loading or index < 0:
            return
        try:
            candidate = self.staged_workspace()
            candidate.selected_profile = index
            self.workspace = candidate
            self.draft = copy.deepcopy(candidate.profiles[index].settings)
            self.load_pages()
            self.draft_changed()
            self.set_status('Local profile loaded into draft. Apply writes it to the connected mouse.')
        except Exception as exc:
            self.update_profiles()
            self.set_status(str(exc), error=True)

    def rename_profile(self):
        profile = self.workspace.profiles[self.workspace.selected_profile]
        text, accepted = QInputDialog.getText(self, 'Rename local profile', 'Name', text=profile.name)
        if accepted:
            from ..domain import validate_name
            try:
                validate_name(text)
                profile.name = text
                self.update_profiles()
                self.set_status('Profile renamed locally. Save workspace to keep the name.')
            except ValidationError as exc:
                self.set_status(str(exc), error=True)

    def draft_changed(self):
        self.dirty = self.snapshot is None or self.draft != self.snapshot.settings or self.macros_dirty
        self.draft_status.setText('Changes staged' if self.dirty else 'Mouse settings read back')
        self.update_actions()

    def macro_changed(self):
        self.macros_dirty = True
        self.draft_changed()

    def set_status(self, text, error=False):
        self.status.setText(text)
        self.status.setObjectName('error' if error else 'muted')
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def update_actions(self):
        available = not self.busy and not self.closing
        for widget in (self.pages, self.connection_bar, self.profile_bar, self.files_bar, self.reset_button):
            widget.setEnabled(available)
        self.connect_button.setEnabled(available and bool(self.devices))
        self.refresh_button.setEnabled(available and self.snapshot is not None)
        self.apply_button.setEnabled(available and self.snapshot is not None and self.dirty)

    def submit(self, operation, *args):
        if self.busy or self.closing:
            return
        self.macros.stop_recording()
        self.busy = True
        self.set_status({'scan': 'Looking for mice…', 'connect': 'Reading mouse settings…',
                         'refresh': 'Refreshing mouse status…', 'apply': 'Applying and checking mouse settings…'}[operation])
        self.update_actions()
        self.requested.emit(operation, args)

    def scan_devices(self):
        self.submit('scan')

    def connect_device(self, checked=False, *, preserve_draft=False):
        if self.busy or self.closing:
            return
        index = self.device_picker.currentIndex()
        if 0 <= index < len(self.devices):
            self._preserve_connect_draft = preserve_draft
            self.submit('connect', self.devices[index])

    def refresh_device(self):
        if self.snapshot:
            try:
                self.macros.commit_editor()
                self.submit('refresh')
            except ValidationError as exc:
                self.set_status(str(exc), error=True)

    def apply_draft(self):
        if self.busy or self.closing or self.snapshot is None:
            return
        try:
            candidate = self.staged_workspace()
            self._pending_local_macro_ids = {binding.macro_id for binding in self.draft.bindings
                                             if binding.action == 'macro'}
            self.submit('apply', copy.deepcopy(self.draft), copy.deepcopy(candidate.macros))
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def operation_finished(self, operation, result, error):
        self.busy = False
        if self.closing:
            return
        if error:
            if not self.service.connected:
                self.snapshot = None
                self.device_summary.setText('Mouse disconnected · draft preserved')
                self.sensitivity.battery.setText('—')
            if isinstance(error, ApplyError) and error.partial:
                self.set_status(f'The mouse may contain some changes ({error.completed_writes} confirmed). Reconnect to read its state. {error}', error=True)
            else:
                self.set_status(f'{error}', error=True)
            self.draft_changed()
            return
        if operation == 'scan':
            self.devices = result
            self.device_picker.clear()
            for device in result:
                self.device_picker.addItem(f'{device.name} · {device.serial or device.id}')
            self.set_status(f'{len(result)} mouse found. Choose Read mouse to load its current settings.' if result else
                            'No supported mouse found. Check USB connection and Linux hidraw permissions.')
            self.update_actions()
            if self.demo and len(result) == 1:
                self.connect_device(preserve_draft=self._startup_autoconnect and self._saved_draft_loaded)
            self._startup_autoconnect = False
            return
        snapshot, device_macros = result
        self.snapshot = snapshot
        if operation == 'connect':
            self._device_macro_aliases.clear()
        self.adopt_device_macros(device_macros, snapshot.settings,
                                local_ids=self._pending_local_macro_ids if operation == 'apply' else ())
        # Adoption only reuses local metadata when its encoded body/mode matches
        # this readback; unapplied library edits cannot become snapshot bodies.
        snapshot_ids = {binding.macro_id for binding in snapshot.settings.bindings if binding.action == 'macro'}
        self._snapshot_macros = copy.deepcopy([macro for macro in self.workspace.macros if macro.id in snapshot_ids])
        preserve_draft = operation == 'connect' and self._preserve_connect_draft
        if operation == 'apply' or operation == 'connect' and not preserve_draft:
            self.draft = copy.deepcopy(snapshot.settings)
            self.macros_dirty = False
            self.load_pages()
        else:
            self.macros.load(self.workspace.macros)
        self.device_summary.setText(f'AJ199 · {snapshot.device.name} · Device profile {snapshot.current_profile} · '
                                    + ('Demo connection' if self.demo else 'Charging' if snapshot.charging else 'USB connected'))
        self.sensitivity.battery.setText('Unavailable' if snapshot.battery_percent is None else f'{snapshot.battery_percent}%')
        self.draft_changed()
        self.set_status('Saved local profile preserved in draft. Apply writes it to the demo mouse.' if preserve_draft else
                        'Settings applied and read back. Save workspace to keep local profiles and macros.' if operation == 'apply' else
                        'Mouse settings read. Local profiles and library stay on this computer.' if operation == 'connect' else
                        'Mouse status refreshed. Draft edits preserved.')

    @staticmethod
    def _macro_matches_readback(candidate, readback):
        if candidate is None:
            return False
        try:
            return (candidate.loop_mode == readback.loop_mode
                    and (candidate.loop_mode != 'count' or candidate.repeat == readback.repeat)
                    and encode_macro(candidate) == encode_macro(readback))
        except ValidationError:
            return False  # a valid local-only macro need not encode for hardware

    def adopt_device_macros(self, macros, settings, *, local_ids=()):
        # IDs carry no provenance: local IDs span uint32, including device-like
        # values. Record the actual readback identity and its library alias.
        used = {macro.id for macro in self.workspace.macros} | {macro.id for macro in macros}
        remapped = {}
        for macro in macros:
            device_id = macro.id
            existing = next((m for m in self.workspace.macros if m.id == macro.id), None)
            alias = self._device_macro_aliases.get(device_id)
            aliased = next((m for m in self.workspace.macros if alias and m.id == alias[1]), None)
            if device_id in local_ids and self._macro_matches_readback(existing, macro):
                library_id = existing.id  # retain full host name/timing metadata
            elif alias and alias[0] == macro and self._macro_matches_readback(aliased, macro):
                library_id = alias[1]
            else:
                equivalent = None
                for candidate in self.workspace.macros:
                    comparable = copy.deepcopy(macro)
                    comparable.id = candidate.id
                    if comparable == candidate:
                        equivalent = candidate
                        break
                if equivalent is not None:
                    library_id = equivalent.id
                else:
                    library_id = device_id if existing is None else next(value for value in range(1, len(used) + 2) if value not in used)
                    adopted = copy.deepcopy(macro)
                    adopted.id = library_id
                    self.workspace.macros.append(adopted)
                    used.add(library_id)
            self._device_macro_aliases[device_id] = (copy.deepcopy(macro), library_id)
            remapped[device_id] = library_id
        for binding in settings.bindings:
            if binding.action == 'macro' and binding.macro_id in remapped:
                binding.macro_id = remapped[binding.macro_id]

    def reset_draft(self):
        if self.snapshot:
            # Library edits/imports may remove or reuse snapshot IDs. Restore the
            # retained bodies without overwriting any current local entry.
            before = copy.deepcopy(self.snapshot.settings.bindings)
            self.workspace.macros = self.merge_imported_macros(self.snapshot.settings, self._snapshot_macros)
            remapped = {old.macro_id: new.macro_id for old, new in zip(before, self.snapshot.settings.bindings)
                        if old.action == 'macro'}
            for macro in self._snapshot_macros:
                macro.id = remapped[macro.id]
            self._device_macro_aliases = {device_id: (body, remapped.get(library_id, library_id))
                                          for device_id, (body, library_id) in self._device_macro_aliases.items()}
        self.draft = copy.deepcopy(self.snapshot.settings if self.snapshot else self.workspace.profiles[self.workspace.selected_profile].settings)
        self.load_pages()
        self.draft_changed()
        self.set_status('Draft reset from last mouse read.' if self.snapshot else 'Draft reset from the local profile.')

    def save_workspace(self):
        try:
            if self.load_error:
                raise ValidationError('The existing workspace is invalid and has been preserved. Export a native backup or restart with another --workspace directory.')
            candidate = self.staged_workspace()
            self.store.save(candidate)
            self.workspace.profiles = candidate.profiles
            self.set_status(f'Workspace saved · {self.store.path}')
        except Exception as exc:
            self.set_status(f'Could not save workspace: {exc}', error=True)

    @staticmethod
    def file_store(path):
        path = Path(path)
        store = ProfileStore(path.parent)
        store.path = path
        return store

    def export_workspace(self, path):
        self.file_store(path).save(self.staged_workspace())
        self.set_status('Native workspace backup exported. All four profiles and the macro library are included.')

    def import_workspace(self, path):
        candidate = self.file_store(path).load()
        self.workspace = candidate
        self._device_macro_aliases.clear()
        self.draft = copy.deepcopy(candidate.profiles[candidate.selected_profile].settings)
        self.macros_dirty = True
        self.load_pages()
        self.update_profiles()
        self.draft_changed()
        self.set_status('Native backup loaded locally. Save workspace to keep it; Apply writes the current draft.')

    def merge_imported_macros(self, settings, macros):
        library = copy.deepcopy(self.workspace.macros)
        macros = copy.deepcopy(macros)
        reserved = {m.id for m in library} | {m.id for m in macros}
        remapped = {}
        for macro in macros:
            existing = next((m for m in library if m.id == macro.id), None)
            if existing and existing != macro:
                old_id = macro.id
                macro.id = next(value for value in range(1, len(reserved) + 2) if value not in reserved)
                reserved.add(macro.id)
                remapped[old_id] = macro.id
            if existing is None or existing != macro:
                library.append(macro)
        for binding in settings.bindings:
            if binding.action == 'macro' and binding.macro_id in remapped:
                binding.macro_id = remapped[binding.macro_id]
        return library

    def import_dialog(self):
        path, selected = QFileDialog.getOpenFileName(self, 'Import settings', '',
            'Native workspace (*.json);;Legacy profile (*.jma);;Legacy profile set (*.dct)')
        if not path:
            return
        try:
            self.macros.commit_editor()
            if Path(path).suffix.lower() == '.json':
                self.import_workspace(path)
            elif Path(path).suffix.lower() == '.dct':
                profiles = load_dct(path)
                candidate = self.staged_workspace()
                for index, profile in enumerate(profiles):
                    candidate.profiles[index] = profile
                candidate.validate()
                self.workspace = candidate
                self.draft = copy.deepcopy(candidate.profiles[candidate.selected_profile].settings)
                self.load_pages()
                self.update_profiles()
                self.draft_changed()
                self.set_status('Legacy profiles imported locally. Save workspace to keep them.')
            else:
                settings, macros = load_profile(path)
                library = self.merge_imported_macros(settings, macros)
                candidate = copy.deepcopy(self.workspace)
                candidate.macros = library
                candidate.profiles[candidate.selected_profile].settings = settings
                candidate.validate()
                self.workspace = candidate
                self.draft = settings
                self.macros_dirty = True
                self.load_pages()
                self.draft_changed()
                self.set_status('Legacy profile imported into draft. Some preserved legacy assignments cannot be applied to hardware.')
        except Exception as exc:
            self.set_status(f'Import failed; existing data preserved: {exc}', error=True)

    def export_dialog(self):
        path, selected = QFileDialog.getSaveFileName(self, 'Export settings', 'vela-workspace.json',
            'Native workspace (*.json);;Legacy profile subset (*.jma)')
        if not path:
            return
        try:
            if Path(path).suffix.lower() == '.jma' or 'jma' in selected:
                candidate = self.staged_workspace()
                save_profile(path, self.draft, select_profile_macros(self.draft, candidate.macros))
                self.set_status('Legacy profile exported.')
            else:
                self.export_workspace(path)
        except Exception as exc:
            self.set_status(f'Export failed: {exc}. Choose Native workspace to retain complete profiles and macros.', error=True)

    def macro_message(self, message):
        if message.startswith('delete:'):
            macro_id = int(message.split(':')[1])
            settings = [profile.settings for profile in self.workspace.profiles] + [self.draft]
            if any(binding.action == 'macro' and binding.macro_id == macro_id for setting in settings for binding in setting.bindings):
                self.set_status('This macro is assigned to a button in a local profile or the draft. Change the assignment before deleting it.', error=True)
                return
            self.workspace.macros[:] = [m for m in self.workspace.macros if m.id != macro_id]
            self.macros.load(self.workspace.macros)
            self.macro_changed()
        else:
            self.set_status(message)

    def show_about(self):
        QMessageBox.about(self, 'About Vela',
            'Vela Mouse Studio 0.1.0\n\nIndependent native AJ199 configuration. Original Vela identity; implementation from a written behavioral specification.\n\n'
            'Demo uses the same report service with in-memory hardware. Real hardware writes have not been validated. '
            'Firmware updates and unknown sensor features are unavailable.\n\n'
            'Profiles are local drafts, not proven independent device banks. Macro recording captures only the focused area; '
            'logical keys follow your layout and modifier sides are not distinguished.\n\n'
            'Shutdown waits for current I/O and closes the handle. An indefinitely blocked OS HID call cannot be safely cancelled.\n\n'
            'MIT license for Vela; Qt/PySide6 and HIDAPI retain their own licenses. See README and dependency notices.')

    def closeEvent(self, event):
        if self.thread_stopped:
            event.accept()
            return
        event.ignore()
        if not self.closing:
            self.closing = True
            self.macros.stop_recording()
            self.set_status('Closing after the current device operation finishes…')
            self.update_actions()
            # Queued behind any in-flight transaction; no termination or GUI wait.
            self.stopping.emit()

    def thread_finished(self):
        self.thread_stopped = True
        self.close()
