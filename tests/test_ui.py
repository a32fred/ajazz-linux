"""User workflows against native widgets and the report-level simulator."""
import atexit
import copy
import gc
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import threading
import sys
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from vela.domain import Binding, Macro, MacroEvent, default_workspace
from vela.formats import load_profile
from vela.service import MouseService
from vela.simulator import SimulatedTransport
from vela.storage import ProfileStore
from vela.ui.window import MainWindow


APP = QApplication.instance() or QApplication([])

if sys.version_info < (3, 12):
    # Python 3.10 and 3.11 abort in interpreter finalization after three MainWindow fixtures, with every
    # PySide6 tried; the app exits cleanly. Report the real result and skip that finalization.
    _run = unittest.TextTestRunner.run

    def _run_and_exit_cleanly(self, test):
        result = _run(self, test)
        sys.stdout.flush()
        sys.stderr.flush()
        atexit.register(os._exit, 0 if result.wasSuccessful() else 1)
        return result

    unittest.TextTestRunner.run = _run_and_exit_cleanly


def until(predicate, timeout=5000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        APP.processEvents()
        QTest.qWait(5)
    if not predicate():
        raise AssertionError('Timed out waiting for native UI operation')


class SlowSimulator(SimulatedTransport):
    delay = 0
    thread_ids = None

    def send(self, packet):
        if self.thread_ids is not None:
            self.thread_ids.add(threading.get_ident())
        if self.delay:
            time.sleep(self.delay)
        return super().send(packet)


class UiTests(unittest.TestCase):
    def test_compact_shell_and_macro_columns_reflow(self):
        from PySide6.QtWidgets import QBoxLayout
        self.window.navigation.setCurrentRow(3)
        self.window.resize(1100, 800)
        APP.processEvents()
        self.assertEqual(self.window.macros.columns.direction(), QBoxLayout.Direction.LeftToRight)
        self.window.resize(800, 580)
        for _ in range(5):
            APP.processEvents()
        self.assertGreaterEqual(self.window.pages.height(), 340)
        self.assertEqual(self.window.macros.columns.direction(), QBoxLayout.Direction.LeftToRight)
        self.assertEqual(self.window.pages.currentWidget().horizontalScrollBar().maximum(), 0)

    def test_real_mode_automatically_reads_available_mouse(self):
        self.close_window()
        self.window = MainWindow(service=self.service, store=self.store, demo=False)
        self.window.show()
        until(lambda: self.window.snapshot is not None and not self.window.busy)
        self.assertEqual(self.window.snapshot.device.id, self.transport.device.id)
        self.assertFalse(any(packet[1] == 7 for packet in self.transport.sent))

    def test_mouse_diagram_opens_assignment_for_each_button(self):
        self.window.navigation.setCurrentRow(1)
        APP.processEvents()
        from vela.ui.buttons import BindingDialog
        with patch.object(BindingDialog, 'exec', return_value=0) as edit:
            for control in self.window.buttons.diagram.controls:
                QTest.mouseClick(control, Qt.MouseButton.LeftButton)
            self.assertEqual(edit.call_count, 6)
            control = self.window.buttons.diagram.controls[3]
            control.setFocus()
            QTest.keyClick(control, Qt.Key.Key_Space)
            self.assertEqual(edit.call_count, 7)

    def test_automatic_reconnection_preserves_pending_draft(self):
        self.window.snapshot = None
        self.service.disconnect()
        self.window.sensitivity.x_dpi.setValue(3200)
        self.window.scan_devices()
        until(lambda: self.window.snapshot is not None and not self.window.busy)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertEqual(self.window.snapshot.settings.stages[0].x, 800)

    def test_shortcut_capture_replaces_released_keys(self):
        from vela.ui.buttons import KeyCapture
        capture = KeyCapture()
        QTest.keyClick(capture, Qt.Key.Key_K)
        QTest.keyClick(capture, Qt.Key.Key_L)
        self.assertEqual(capture.keys, [15])
        self.assertEqual(capture.text(), 'L')

    def test_shortcut_capture_keeps_only_overlapping_keys(self):
        from vela.ui.buttons import KeyCapture
        capture = KeyCapture()
        QTest.keyPress(capture, Qt.Key.Key_Control)
        QTest.keyClick(capture, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(capture, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        QTest.keyRelease(capture, Qt.Key.Key_Control)
        self.assertEqual(capture.keys, [15])
        self.assertEqual(capture.text(), 'Ctrl + L')

    def test_dpi_stage_event_updates_the_stage_and_notifies(self):
        shown = []
        self.window.notifier.show = lambda title, body='', **kwargs: shown.append((title, body)) or True
        stages = self.window.snapshot.settings.stages
        self.window.on_dpi_stage(1)
        self.assertEqual(self.window.snapshot.settings.active_stage, 1)
        self.assertEqual(self.window.draft.active_stage, 1)
        self.assertFalse(self.window.dirty)
        self.assertEqual(shown, [('DPI stage 2', f'{stages[1].x} DPI')])
        self.window.on_dpi_stage(99)
        self.assertEqual(len(shown), 1)

    def test_battery_warnings_fire_once_per_level_and_rearm(self):
        shown = []
        self.window.notifier.show = lambda title, body='', **kwargs: shown.append(body) or True
        for percent, charging in ((50, False), (19, False), (18, False), (9, False), (8, False),
                                  (35, False), (15, False), (15, True), (12, False), (None, False)):
            self.window.check_battery(percent, charging)
        self.assertEqual(shown, ['19% left', '9% left', '15% left', '12% left'])

    def test_scroll_light_controls_edit_the_draft_and_keep_unknown_modes(self):
        from vela.domain import DpiEffect
        page = self.window.lighting
        draft = copy.deepcopy(self.window.draft)
        draft.dpi_effect = DpiEffect(1, 10, 3)
        page.load(draft)
        self.assertFalse(page.dpi_speed.isEnabled())
        page.dpi_mode.setCurrentIndex(page.dpi_mode.findData(2))
        self.assertEqual(draft.dpi_effect.mode, 2)
        self.assertTrue(page.dpi_speed.isEnabled())
        page.dpi_speed.setValue(7)
        page.dpi_brightness.setValue(4)
        self.assertEqual((draft.dpi_effect.param, draft.dpi_effect.brightness), (7, 4))
        page.dpi_mode.setCurrentIndex(page.dpi_mode.findData(0))
        self.assertFalse(page.dpi_brightness.isEnabled())
        other = copy.deepcopy(self.window.draft)
        other.dpi_effect = DpiEffect(5, 10, 3)
        page.load(other)
        self.assertEqual(page.dpi_mode.currentData(), 5)
        page.dpi_brightness.setValue(6)
        self.assertEqual((other.dpi_effect.mode, other.dpi_effect.brightness), (5, 6))
        page.load(copy.deepcopy(self.window.draft))
        self.assertFalse(page.dpi_mode.isEnabled())

    def test_unverified_lighting_controls_require_explicit_opt_in(self):
        self.assertTrue(self.window.lighting.effect_controls.isHidden())
        self.assertFalse(self.window.lighting.effect_controls.isEnabled())
        self.window.lighting.experimental.setChecked(True)
        self.assertTrue(self.window.lighting.effect_controls.isEnabled())
        self.assertFalse(self.window.lighting.effect_controls.isHidden())

    def test_macro_key_names_roundtrip(self):
        self.window.macros.new_macro()
        self.window.macros.add_event()
        self.window.macros.event_table.item(0, 1).setText('Space')
        self.window.macros.commit_editor()
        self.assertEqual(self.window.macros.current().events[0].code, 0x2c)

    def test_record_button_creates_macro_and_assigns_to_side_button(self):
        self.window.macros.start_recording()
        self.assertIsNotNone(self.window.macros.current())
        QTest.keyClick(self.window.macros.recorder, Qt.Key.Key_A)
        self.window.macros.stop_recording()
        self.window.macros.assign_button.click()
        self.assertEqual(self.window.draft.bindings[3].action, 'macro')
        self.assertEqual(self.window.draft.bindings[3].macro_id, self.window.macros.current_id)

    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.transport = SlowSimulator()
        self.service = MouseService(transport=self.transport)
        self.store = ProfileStore(Path(self.root.name))
        self.window = MainWindow(service=self.service, store=self.store, demo=True)
        self.window.show()
        until(lambda: self.window.snapshot is not None and not self.window.busy)

    def tearDown(self):
        self.close_window()
        self.root.cleanup()

    def close_window(self):
        self.window.close()
        until(lambda: not self.window.io_thread.isRunning())
        self.window.deleteLater()
        # Finish Qt deletion on the GUI thread before the next fixture can run.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertFalse(isValid(self.window))
        del self.window
        gc.collect()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_connect_edit_apply_and_page_switch_preserves_draft(self):
        self.assertIn('DEMO', self.window.mode_badge.text())
        self.assertIn('AJ199', self.window.device_summary.text())
        self.window.sensitivity.x_dpi.setValue(3200)
        for index in range(4):
            self.window.navigation.setCurrentRow(index)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertEqual(self.window.snapshot.settings.stages[0].x, 800)
        QTest.mouseClick(self.window.apply_button, Qt.MouseButton.LeftButton)
        until(lambda: not self.window.busy)
        self.assertEqual(self.window.snapshot.settings.stages[0].x, 3200)
        self.assertFalse(self.window.dirty)

    def test_periodic_read_updates_clean_settings_without_writing(self):
        from vela.protocol import checked
        self.window.poll_timer.stop()
        self.transport.memory[4:6] = checked([1])
        self.transport.sent.clear()
        self.window.poll_device()
        until(lambda: not self.window.polling)
        self.assertEqual(self.window.draft.active_stage, 1)
        self.assertFalse(self.window.dirty)
        self.assertFalse(any(packet[1] == 7 for packet in self.transport.sent))

    def test_periodic_read_leaves_pending_edits_alone(self):
        self.window.poll_timer.stop()
        self.window.sensitivity.x_dpi.setValue(3200)
        self.transport.sent.clear()
        self.window.poll_device()
        APP.processEvents()
        self.assertFalse(self.window.busy)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertEqual(self.transport.sent, [])

    def test_background_poll_keeps_editing_and_macro_recording_alive(self):
        self.window.poll_timer.stop()
        self.transport.delay = .01
        self.window.poll_device()
        self.assertFalse(self.window.busy)
        self.assertTrue(self.window.polling)
        self.assertTrue(self.window.pages.isEnabled())
        self.window.macros.start_recording()
        self.window.sensitivity.x_dpi.setValue(3200)
        until(lambda: not self.window.polling)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertTrue(self.window.macros.recorder.recording)

    def test_apply_during_background_poll_is_not_dropped(self):
        self.window.poll_timer.stop()
        self.transport.delay = .001
        self.window.poll_device()
        self.window.sensitivity.x_dpi.setValue(3200)
        self.window.apply_draft()
        until(lambda: not self.window.busy and not self.window.polling)
        self.assertEqual(self.window.snapshot.settings.stages[0].x, 3200)

    def test_local_profile_macro_and_native_backup_roundtrip(self):
        self.window.macros.new_macro()
        self.window.macros.name_edit.setText('My sequence')
        self.window.macros.add_event()
        self.window.macros.event_table.item(0, 1).setText('4')
        self.window.macros.event_table.item(0, 2).setText('25')
        self.window.save_workspace()
        loaded = self.store.load()
        self.assertEqual(loaded.macros[0].name, 'My sequence')
        self.assertEqual(loaded.macros[0].events[0], MacroEvent('down', 4, 25))
        backup = Path(self.root.name) / 'backup.vela.json'
        self.window.export_workspace(backup)
        self.window.sensitivity.x_dpi.setValue(6400)
        self.window.import_workspace(backup)
        self.assertEqual(self.window.draft.stages[0].x, 800)
        self.assertEqual(self.window.workspace.macros[0].name, 'My sequence')

    def test_slow_io_keeps_event_loop_alive_and_shutdown_closes_handle(self):
        self.transport.delay = .01
        self.transport.thread_ids = set()
        ticks = []
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start()
        self.window.refresh_device()
        self.window.close()
        self.assertTrue(self.window.io_thread.isRunning())
        until(lambda: not self.window.io_thread.isRunning())
        timer.stop()
        self.assertGreater(len(ticks), 5)
        self.assertNotIn(threading.get_ident(), self.transport.thread_ids)
        self.assertFalse(self.transport.is_open)

    def test_apply_failure_preserves_draft_and_reports_partial_state(self):
        self.window.sensitivity.x_dpi.setValue(3200)
        self.transport.fail_after_writes = 0
        self.window.apply_draft()
        until(lambda: not self.window.busy)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertIsNone(self.window.snapshot)
        self.assertIn('may contain', self.window.status.text().lower())

    def test_recorder_captures_only_focused_target_and_hid_codes(self):
        self.window.navigation.setCurrentRow(3)
        self.window.macros.new_macro()
        self.window.macros.start_recording()
        target = self.window.macros.recorder
        QTest.keyPress(target, Qt.Key.Key_A)
        QTest.keyRelease(target, Qt.Key.Key_A)
        self.window.macros.stop_recording()
        events = self.window.workspace.macros[0].events
        self.assertEqual([(e.kind, e.code) for e in events], [('down', 4), ('up', 4)])
        QTest.keyClick(self.window.macros.name_edit, Qt.Key.Key_B)
        self.assertEqual(len(self.window.workspace.macros[0].events), 2)

    def test_reading_device_macros_keeps_local_library_originals(self):
        original = Macro(7, 'Original full name exceeds fifteen', [MacroEvent('down', 4), MacroEvent('up', 4)])
        self.window.workspace.macros.append(copy.deepcopy(original))
        self.window.draft.bindings[3] = Binding('macro', macro_id=7)
        self.window.apply_draft()
        until(lambda: not self.window.busy)
        self.assertEqual(self.window.workspace.macros[0], original)
        self.assertEqual(self.window.draft.bindings[3].macro_id, 7)

    def test_import_macro_id_collisions_do_not_rebind_another_import(self):
        self.window.workspace.macros.append(Macro(1, 'Local', []))
        settings = copy.deepcopy(self.window.draft)
        settings.bindings[3] = Binding('macro', macro_id=1)
        settings.bindings[4] = Binding('macro', macro_id=2)
        incoming = [Macro(1, 'Imported one', []), Macro(2, 'Imported two', [])]
        library = self.window.merge_imported_macros(settings, incoming)
        by_id = {m.id: m.name for m in library}
        self.assertEqual(by_id[settings.bindings[3].macro_id], 'Imported one')
        self.assertEqual(by_id[settings.bindings[4].macro_id], 'Imported two')

    def test_invalid_event_cannot_overwrite_saved_workspace(self):
        self.window.macros.new_macro()
        self.window.macros.add_event()
        self.window.save_workspace()
        before = self.store.path.read_bytes()
        self.window.macros.event_table.item(0, 2).setText('65536')
        self.window.save_workspace()
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertIn('65535', self.window.status.text())

    def test_device_macro_remains_available_after_refresh_and_reset(self):
        settings = copy.deepcopy(self.window.draft)
        settings.bindings[4] = Binding('macro', macro_id=99)
        # External simulator change, on a separate completed service transaction.
        self.service.apply(settings, [Macro(99, 'From device', [MacroEvent('down', 4)])])
        self.window.refresh_device()
        until(lambda: not self.window.busy)
        self.window.reset_draft()
        self.window.save_workspace()
        saved = self.store.load()
        self.assertIn(saved.profiles[0].settings.bindings[4].macro_id, {m.id for m in saved.macros})

    def test_recording_limit_does_not_add_release_without_press(self):
        self.window.navigation.setCurrentRow(3)
        self.window.macros.new_macro()
        macro = self.window.workspace.macros[0]
        macro.events = [MacroEvent('move', dx=1) for _ in range(69)]
        self.window.macros.load_editor()
        self.window.macros.start_recording()
        QTest.keyPress(self.window.macros.recorder, Qt.Key.Key_A)
        QTest.keyRelease(self.window.macros.recorder, Qt.Key.Key_A)
        self.assertFalse(self.window.macros.recorder.recording)
        self.assertEqual(len(macro.events), 69)
        self.assertTrue(all(e.kind == 'move' for e in macro.events))

    def read_macro_from_simulator(self):
        settings = copy.deepcopy(self.window.draft)
        settings.bindings[4] = Binding('macro', macro_id=99)
        self.service.apply(settings, [Macro(99, 'Device sequence', [MacroEvent('down', 4)])])
        self.window.refresh_device()
        until(lambda: not self.window.busy)
        self.window.reset_draft()
        return self.window.draft.bindings[4].macro_id

    def test_reset_restores_deleted_snapshot_macro_and_can_save_apply(self):
        macro_id = self.read_macro_from_simulator()
        self.window.draft.bindings[4] = Binding('left')
        self.window.load_pages()
        self.window.macro_message(f'delete:{macro_id}')
        self.assertEqual(self.window.workspace.macros, [])
        self.window.reset_draft()
        self.assertEqual([m.name for m in self.window.workspace.macros], ['Device sequence'])
        self.window.save_workspace()
        self.assertEqual(self.store.load().profiles[0].settings.bindings[4].macro_id, macro_id)
        self.window.apply_draft()
        until(lambda: not self.window.busy)
        self.assertIsNotNone(self.window.snapshot)
        self.assertEqual(self.window.snapshot.settings.bindings[4].macro_id, macro_id)

    def test_reset_uses_device_events_after_unapplied_macro_edit_and_refresh(self):
        macro_id = self.read_macro_from_simulator()
        writes_before = self.transport.write_count
        self.window.macros.event_table.item(0, 1).setText('5')
        self.window.refresh_device()
        until(lambda: not self.window.busy)
        edited = next(m for m in self.window.workspace.macros if m.id == macro_id)
        self.assertEqual(edited.events, [MacroEvent('down', 5)])
        self.window.draft.bindings[4] = Binding('left')
        self.window.load_pages()
        self.window.macro_message(f'delete:{macro_id}')
        self.assertNotIn(macro_id, {m.id for m in self.window.workspace.macros})
        self.window.reset_draft()
        restored_id = self.window.draft.bindings[4].macro_id
        restored = next(m for m in self.window.workspace.macros if m.id == restored_id)
        self.assertEqual(restored.events, [MacroEvent('down', 4)])
        self.assertEqual(self.service.macros[0].events, [MacroEvent('down', 4)])
        self.assertEqual(self.transport.write_count, writes_before)

    def test_reset_after_native_import_remaps_snapshot_macro_collision(self):
        macro_id = self.read_macro_from_simulator()
        imported = default_workspace()
        imported.macros = [Macro(macro_id, 'Imported local', []), Macro(1, 'Keep ID one', [])]
        imported.profiles[1].settings.bindings[3] = Binding('macro', macro_id=macro_id)
        path = Path(self.root.name) / 'import.json'
        self.window.file_store(path).save(imported)
        self.window.import_workspace(path)
        self.window.reset_draft()
        restored_id = self.window.draft.bindings[4].macro_id
        self.assertNotEqual(restored_id, macro_id)
        self.assertEqual(self.window.workspace.macros[:2], imported.macros)
        self.assertEqual(self.window.workspace.macros[2].name, 'Device sequence')
        self.window.save_workspace()
        self.assertEqual(self.store.load().profiles[1], imported.profiles[1])
        for _ in range(2):
            self.window.reset_draft()
            self.window.refresh_device()
            until(lambda: not self.window.busy)
            self.assertEqual(self.window.snapshot.settings.bindings[4].macro_id, restored_id)
            self.assertEqual(len(self.window.workspace.macros), 3)

    def export_jma_from_dialog(self, path):
        with patch('vela.ui.window.QFileDialog.getSaveFileName', return_value=(str(path), 'Legacy profile subset (*.jma)')):
            self.window.export_dialog()
        self.assertTrue(path.exists(), self.window.status.text())
        return load_profile(path)

    def test_jma_ui_export_ignores_eleven_unrelated_macros(self):
        self.window.draft.bindings = [Binding('left') for _ in range(6)]
        self.window.workspace.macros = [Macro(i, f'Unrelated {i}', []) for i in range(1, 12)]
        self.window.load_pages()
        settings, macros = self.export_jma_from_dialog(Path(self.root.name) / 'subset.jma')
        self.assertEqual(settings, self.window.draft)
        self.assertEqual(macros, [])
        self.assertEqual(len(self.window.workspace.macros), 11)

    def test_jma_ui_export_still_rejects_unevidenced_default_bindings(self):
        path = Path(self.root.name) / 'default.jma'
        path.write_bytes(b'Existing export')
        with patch('vela.ui.window.QFileDialog.getSaveFileName', return_value=(str(path), 'Legacy profile subset (*.jma)')):
            self.window.export_dialog()
        self.assertEqual(path.read_bytes(), b'Existing export')
        self.assertIn('cannot represent', self.window.status.text())

    def test_jma_ui_export_ignores_unrepresentable_unrelated_events(self):
        self.window.draft.bindings = [Binding('left') for _ in range(6)]
        self.window.workspace.macros = [Macro(1, 'Keypad Enter', [MacroEvent('down', 0x58)])]
        self.window.load_pages()
        _, macros = self.export_jma_from_dialog(Path(self.root.name) / 'subset.jma')
        self.assertEqual(macros, [])

    def test_jma_ui_export_retains_opaque_other_bank_macro_references(self):
        import struct
        from test_formats import fixture_jma
        path = Path(self.root.name) / 'opaque.jma'
        raw = bytearray(fixture_jma())
        struct.pack_into('<III', raw, 0x23c, 0x05000000, 1, 123)
        path.write_bytes(raw)
        settings, macros = load_profile(path)
        # Remove the selected bank's reference: only the opaque bank needs it.
        settings.bindings[3] = Binding('left')
        self.window.draft = settings
        self.window.workspace.macros = macros + [Macro(i, f'Unrelated {i}', []) for i in range(1, 12)]
        self.window.load_pages()
        _, exported = self.export_jma_from_dialog(Path(self.root.name) / 'subset.jma')
        self.assertEqual([m.id for m in exported], [123])
        self.assertEqual((Path(self.root.name) / 'subset.jma').read_bytes()[0x23c:0x254], raw[0x23c:0x254])

    def test_demo_window_restart_preserves_saved_selected_profile(self):
        self.window.sensitivity.x_dpi.setValue(3200)
        self.window.save_workspace()
        self.window.close()
        until(lambda: not self.window.io_thread.isRunning())
        self.window.deleteLater()
        APP.processEvents()
        self.transport = SlowSimulator()
        self.service = MouseService(transport=self.transport)
        self.window = MainWindow(service=self.service, store=self.store, demo=True)
        self.window.show()
        until(lambda: self.window.snapshot is not None and not self.window.busy)
        self.assertEqual(self.window.snapshot.settings.stages[0].x, 800)
        self.assertEqual(self.window.draft.stages[0].x, 3200)
        self.assertEqual(self.window.sensitivity.x_dpi.value(), 3200)
        self.assertTrue(self.window.dirty)
        self.window.save_workspace()
        self.assertEqual(self.store.load().profiles[0].settings.stages[0].x, 3200)
        self.assertEqual(self.transport.write_count, 0)

    def test_high_local_macro_id_preserves_name_and_identity_on_refresh(self):
        original = Macro(0xf0000000, 'Original full name exceeds fifteen',
                         [MacroEvent('down', 4), MacroEvent('up', 4)])
        self.window.workspace.macros.append(copy.deepcopy(original))
        self.window.draft.bindings[3] = Binding('macro', macro_id=original.id)
        self.window.apply_draft()
        until(lambda: not self.window.busy)
        for _ in range(3):
            self.assertEqual(self.window.workspace.macros, [original])
            self.assertEqual(self.window.draft.bindings[3].macro_id, original.id)
            self.assertEqual(self.window.snapshot.settings.bindings[3].macro_id, original.id)
            self.assertFalse(self.window.dirty)
            self.window.refresh_device()
            until(lambda: not self.window.busy)
            self.window.reset_draft()

    def test_refreshed_device_macro_reuses_collision_alias(self):
        local = Macro(99, 'Unrelated local original', [])
        self.window.workspace.macros.append(copy.deepcopy(local))
        settings = copy.deepcopy(self.window.draft)
        settings.bindings[4] = Binding('macro', macro_id=99)
        self.service.apply(settings, [Macro(99, 'Device sequence', [MacroEvent('down', 4)])])
        self.window.refresh_device()
        until(lambda: not self.window.busy)
        adopted_id = self.window.snapshot.settings.bindings[4].macro_id
        self.assertNotEqual(adopted_id, 99)
        self.window.reset_draft()
        for _ in range(3):
            self.window.refresh_device()
            until(lambda: not self.window.busy)
            self.assertEqual(len(self.window.workspace.macros), 2)
            self.assertEqual(self.window.workspace.macros[0], local)
            self.assertEqual(self.window.snapshot.settings.bindings[4].macro_id, adopted_id)
            self.assertEqual(self.window.draft.bindings[4].macro_id, adopted_id)
            self.assertFalse(self.window.dirty)


if __name__ == '__main__':
    unittest.main()
